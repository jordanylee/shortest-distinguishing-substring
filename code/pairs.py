"""Run shortest-distinguishing-string comparisons for every unordered pair in a batch."""

from __future__ import annotations

import gzip
import json
import logging
import os
import platform
import re
import shutil
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from dfa_stats import minimal_size, reachable_states
from distinguish import shortest_distinguishing
from loader import load_batch

log = logging.getLogger(__name__)

RESULTS_SCHEMA_VERSION = 1
PAIRING_SCHEME = "all unordered within-batch pairs, a<b by id"
PAIR_KEY = ("(a, b): the two DFA record ids from the source batch with a < b; "
            "identical to the key used by similarity-metric results")
PROGRESS_EVERY = 25_000
_RESULTS_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$")
_ALPHABET_DIR_RE = re.compile(r"^alphabet_(\d+)$")
_STATES_DIR_RE = re.compile(r"^states_(\d+)$")
REPO_ROOT = Path(__file__).resolve().parent.parent


def new_results_id(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%d_%H-%M-%S-%f_UTC")


def _git_info() -> dict:
    def run(*args: str) -> str | None:
        try:
            return subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True,
                                  text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    commit = run("rev-parse", "HEAD")
    status = run("status", "--porcelain", "--untracked-files=no")
    return {"repo_commit": commit, "repo_dirty": None if status is None else bool(status)}


class _JsonlWriter:
    """Line writer for plain or gzip JSON Lines. Gzip output omits name/mtime so it is reproducible."""

    def __init__(self, path: Path, compress: bool):
        self._raw = open(path, "wb")
        self._f = gzip.GzipFile(filename="", mode="wb", fileobj=self._raw, mtime=0) if compress else self._raw

    def write(self, obj) -> None:
        self._f.write((json.dumps(obj, separators=(",", ":")) + "\n").encode("utf-8"))

    def close(self) -> None:
        if self._f is not self._raw:
            self._f.close()
        self._raw.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def run_batch(run_dir: Path, results_id: str | None = None, compress: bool = True) -> Path:
    """Compare all pairs in one batch; return the completed results directory."""
    run_dir = Path(run_dir)
    started = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    results_id = results_id or new_results_id(started)
    if not _RESULTS_ID_RE.match(results_id):
        raise ValueError(f"invalid results_id {results_id!r}")

    batch = load_batch(run_dir)
    out_dir = run_dir / "pairs" / results_id
    part_dir = run_dir / "pairs" / f"{results_id}.part"
    for d in (out_dir, part_dir):
        if d.exists():
            msg = f"results directory already exists, refusing to overwrite: {d}"
            log.error(msg)
            raise FileExistsError(msg)
    part_dir.mkdir(parents=True)
    try:
        return _run_batch_into(run_dir, batch, results_id, out_dir, part_dir, compress, started, t0)
    except BaseException:
        # A failed or interrupted run leaves no partial results behind (*.part/ is gitignored,
        # so a leftover would be invisible). A hard kill can still skip this.
        shutil.rmtree(part_dir, ignore_errors=True)
        raise


def _run_batch_into(run_dir: Path, batch, results_id: str, out_dir: Path, part_dir: Path,
                    compress: bool, started: datetime, t0: float) -> Path:
    ext = ".jsonl.gz" if compress else ".jsonl"
    stats_name, pairs_name = f"dfa_stats{ext}", f"pairs{ext}"
    k = len(batch.alphabet)
    dfas = batch.dfas
    n = len(dfas)
    expected_pairs = n * (n - 1) // 2
    # load_batch already validated every row's width, so the per-pair check is skipped below.
    log.info("%s: %d DFAs, alphabet %s, %d states, %d pairs -> %s",
             run_dir, n, list(batch.alphabet), batch.n_states, expected_pairs, out_dir)

    minimal_hist: Counter = Counter()
    reachable_hist: Counter = Counter()
    with _JsonlWriter(part_dir / stats_name, compress) as w:
        for d in dfas:
            r, m = len(reachable_states(d)), minimal_size(d, k)
            reachable_hist[r] += 1
            minimal_hist[m] += 1
            w.write({"id": d.id, "n_states": len(d.delta), "reachable": r, "minimal": m})

    alphabet = batch.alphabet
    length_hist: Counter = Counter()
    n_equiv = 0
    done = 0
    with _JsonlWriter(part_dir / pairs_name, compress) as w:
        for i in range(n):
            a = dfas[i]
            for j in range(i + 1, n):
                b = dfas[j]
                res = shortest_distinguishing(a, b, k, check=False)
                if res.length is None:
                    n_equiv += 1
                    witness = None
                else:
                    length_hist[res.length] += 1
                    witness = [alphabet[s] for s in res.witness]
                lo, hi = (a, b) if a.id < b.id else (b, a)
                w.write({"a": lo.id, "b": hi.id, "length": res.length, "witness": witness})
                done += 1
                if done % PROGRESS_EVERY == 0:
                    log.info("  %d / %d pairs", done, expected_pairs)

    finished = datetime.now(timezone.utc)
    manifest = {
        "schema_version": RESULTS_SCHEMA_VERSION,
        "results_id": results_id,
        "source_run_id": batch.run_id,
        "source_run_dir": os.path.relpath(run_dir.resolve(), REPO_ROOT),
        "source_sha256": batch.input_sha256,
        "alphabet": list(batch.alphabet),
        "alphabet_size": k,
        "state_count": batch.n_states,
        "dfa_count": n,
        "pairing_scheme": PAIRING_SCHEME,
        "pair_key": PAIR_KEY,
        "expected_pair_count": expected_pairs,
        "pair_count": done,
        "pairs_file": pairs_name,
        "pairs_layout": {"a": "DFA id (smaller)", "b": "DFA id (larger)",
                         "length": "shortest distinguishing length, null if equivalent",
                         "witness": "shortlex-smallest shortest distinguishing string as a list "
                                    "of alphabet symbols, null if equivalent"},
        "dfa_stats_file": stats_name,
        "dfa_stats_layout": {"id": "DFA id", "n_states": "raw state count",
                             "reachable": "states reachable from the initial state",
                             "minimal": "states in the minimal complete DFA"},
        "compression": "gzip" if compress else "none",
        "equivalent_pair_count": n_equiv,
        "length_zero_pair_count": length_hist.get(0, 0),
        "max_finite_length": max(length_hist) if length_hist else None,
        "length_histogram": {str(L): c for L, c in sorted(length_hist.items())},
        "reachable_histogram": {str(r): c for r, c in sorted(reachable_hist.items())},
        "minimal_histogram": {str(m): c for m, c in sorted(minimal_hist.items())},
        "witness_rule": "BFS over state pairs from (initial, initial), symbols expanded in "
                        "manifest alphabet order, visited marked at enqueue",
        **_git_info(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "started_utc": started.isoformat(),
        "finished_utc": finished.isoformat(),
        "elapsed_seconds": round(time.perf_counter() - t0, 3),
        "status": "complete",  # keep last
    }
    with open(part_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    part_dir.rename(out_dir)
    log.info("%s: done in %.2fs, %d equivalent, max length %s",
             out_dir, manifest["elapsed_seconds"], n_equiv, manifest["max_finite_length"])
    return out_dir


def find_run_dirs(run_id: str, data_root: Path, alphabet_sizes=None, state_counts=None) -> list[Path]:
    """Return data/alphabet_<A>/states_<S>/<run_id>/ directories, sorted by (A, S)."""
    found = []
    for d in Path(data_root).glob(f"alphabet_*/states_*/{run_id}"):
        if not d.is_dir():
            continue
        ma = _ALPHABET_DIR_RE.match(d.parent.parent.name)
        ms = _STATES_DIR_RE.match(d.parent.name)
        if not (ma and ms):
            log.warning("skipping directory with non-numeric alphabet/states suffix: %s", d)
            continue
        a, s = int(ma.group(1)), int(ms.group(1))
        if alphabet_sizes is not None and a not in alphabet_sizes:
            continue
        if state_counts is not None and s not in state_counts:
            continue
        found.append((a, s, d))
    return [d for _, _, d in sorted(found)]


def run_all(run_id: str, data_root: Path, results_id: str | None = None,
            alphabet_sizes=None, state_counts=None, compress: bool = True) -> list[Path]:
    """Run every batch of `run_id` under `data_root` with one shared results_id."""
    run_dirs = find_run_dirs(run_id, data_root, alphabet_sizes, state_counts)
    if not run_dirs:
        msg = f"no batches found for run {run_id!r} under {data_root}"
        log.error(msg)
        raise FileNotFoundError(msg)
    results_id = results_id or new_results_id()
    log.info("run %s: %d batches, results_id %s", run_id, len(run_dirs), results_id)
    return [run_batch(d, results_id, compress) for d in run_dirs]

