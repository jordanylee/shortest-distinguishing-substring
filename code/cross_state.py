"""Optional all-pairs comparisons between 10-, 20-, and 30-state batches."""

import hashlib
import json
import logging
import platform
import random
import shutil
import time
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

from dfa_stats import minimal_size, reachable_states
from experiments import _pair_record, _results_id, select_batches
from loader import AlphabetMismatchError, load_batch
from pairs import _git_info, _JsonlWriter
from similarity_metrics import distribution, validate_horizon

STATE_COUNTS = (10, 20, 30)
log = logging.getLogger(__name__)


def _groups(run_id, data_root, alphabet_sizes):
    groups = {}
    for path in select_batches(run_id, data_root, alphabet_sizes, STATE_COUNTS):
        batch = load_batch(path)
        if batch.run_id != run_id or path.parent.name != f"states_{batch.n_states}" or (
                path.parent.parent.name != f"alphabet_{len(batch.alphabet)}"):
            raise ValueError(f"source manifest does not match selected path: {path}")
        groups.setdefault(len(batch.alphabet), {})[batch.n_states] = batch
    if alphabet_sizes is not None and set(alphabet_sizes) - groups.keys():
        raise FileNotFoundError("some selected alphabet sizes have no batches")
    for size, batches in sorted(groups.items()):
        missing = set(STATE_COUNTS) - batches.keys()
        if missing:
            raise FileNotFoundError(f"alphabet {size}: missing state counts {sorted(missing)}")
        ordered = [batches[n] for n in STATE_COUNTS]
        if any(b.alphabet != ordered[0].alphabet for b in ordered):
            raise AlphabetMismatchError(f"alphabet {size}: batches must use identical symbol order")
        yield from combinations(ordered, 2)


def _description(a, b):
    return {"alphabet_size": len(a.alphabet), "state_count_a": a.n_states,
            "state_count_b": b.n_states, "dfa_count_a": len(a.dfas),
            "dfa_count_b": len(b.dfas), "pair_count": len(a.dfas) * len(b.dfas)}


def preview(run_id, data_root, alphabet_sizes=None):
    """Validate every source and count Cartesian products, ignoring states 15/25."""
    return [_description(a, b) for a, b in _groups(run_id, data_root, alphabet_sizes)]


def benchmark(run_id, data_root, *, horizon, alphabet_sizes=None, sample_pairs=100, seed=42):
    """Uniform sampling without replacement per state combination; no writes."""
    validate_horizon(horizon)
    if type(sample_pairs) is not int or sample_pairs < 1:
        raise ValueError("sample_pairs must be a positive integer")
    rng = random.Random(seed)
    rows = []
    for a, b in _groups(run_id, data_root, alphabet_sizes):
        total = len(a.dfas) * len(b.dfas)
        ranks = rng.sample(range(total), min(sample_pairs, total))
        started = time.perf_counter()
        for rank in ranks:
            i, j = divmod(rank, len(b.dfas))
            _pair_record(a.dfas[i], b.dfas[j], a.alphabet, "both", horizon, sort_ids=False)
        elapsed = time.perf_counter() - started
        rows.append({**_description(a, b), "sample_pairs": len(ranks),
                     "sample_seconds": elapsed,
                     "estimated_pair_seconds": elapsed * total / len(ranks) if ranks else 0,
                     "seed": seed, "horizon": horizon})
    return rows


def _write_group(a, b, out, horizon, compress):
    part = out.with_name(out.name + ".part")
    part.mkdir(parents=True)
    started = datetime.now(timezone.utc)
    clock = time.perf_counter()
    suffix = ".jsonl.gz" if compress else ".jsonl"
    pairs_file, stats_file = "pairs" + suffix, "dfa_stats" + suffix
    lengths, reachable, minimal = Counter(), Counter(), Counter()
    count = equivalent = 0
    try:
        with _JsonlWriter(part / stats_file, compress) as writer:
            for batch in (a, b):
                for dfa in batch.dfas:
                    r = len(reachable_states(dfa))
                    m = minimal_size(dfa, len(batch.alphabet))
                    reachable[r] += 1
                    minimal[m] += 1
                    writer.write({"id": dfa.id, "state_count": batch.n_states,
                                  "n_states": len(dfa.delta), "reachable": r, "minimal": m})
        with _JsonlWriter(part / pairs_file, compress) as writer:
            for left in a.dfas:
                for right in b.dfas:
                    row = _pair_record(left, right, a.alphabet, "both", horizon, sort_ids=False)
                    row.update(state_count_a=a.n_states, state_count_b=b.n_states)
                    writer.write(row)
                    count += 1
                    if row["length"] is None:
                        equivalent += 1
                    else:
                        lengths[row["length"]] += 1
                    if count % 1000 == 0:
                        log.info("%s: %d pairs completed", out, count)
        manifest = {
            "schema_version": 1, "results_kind": "cross_state_comparisons",
            "results_id": out.parent.name, "source_run_id": a.run_id,
            "sources": [{"state_count": batch.n_states,
                         "run_dir": str(batch.run_dir.resolve()),
                         "sha256": batch.input_sha256} for batch in (a, b)],
            "alphabet": list(a.alphabet), **_description(a, b),
            "state_count": None, "state_counts": [a.n_states, b.n_states],
            "calculations": "both",
            "pairing_scheme": "Cartesian product of distinct state batches; state_count_a < state_count_b",
            "pair_key": ["source_run_id", "alphabet_size", "state_count_a", "a", "state_count_b", "b"],
            "pairs_layout": {"a": "ID in smaller-state batch; weight_a refers to this DFA",
                             "b": "ID in larger-state batch; weight_b refers to this DFA",
                             "length": "SDS symbol count; null if equivalent",
                             "witness": "shortest witness as alphabet symbol tokens; null if equivalent"},
            "dfa_stats_key": ["state_count", "id"],
            "expected_pair_count": len(a.dfas) * len(b.dfas),
            "pair_count": count, "pairs_file": pairs_file, "dfa_stats_file": stats_file,
            "compression": "gzip" if compress else "none",
            "distribution": distribution(a.alphabet, horizon),
            "interpretation": "descriptive; pairs sharing a DFA are dependent",
            "output_numbers": "metrics converted from exact rationals to binary64 floats",
            "equivalent_pair_count": equivalent, "length_histogram": dict(sorted(lengths.items())),
            "reachable_histogram": dict(sorted(reachable.items())),
            "minimal_histogram": dict(sorted(minimal.items())),
            **_git_info(), "python_version": platform.python_version(),
            "code_sha256": {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                            for name in ("cross_state.py", "experiments.py", "similarity_metrics.py",
                                         "loader.py", "distinguish.py", "dfa_stats.py", "pairs.py")},
            "started_utc": started.isoformat(), "finished_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": time.perf_counter() - clock, "status": "complete"}
        (part / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        part.rename(out)
    except BaseException:
        shutil.rmtree(part, ignore_errors=True)
        raise
    return out


def run_all(run_id, data_root, *, horizon, alphabet_sizes=None, results_id=None, compress=True):
    """Write both metrics and SDS for each distinct state combination, once.

    IDs can coincide across batches: (state_count, id) identifies a DFA.
    Completed combinations survive failure; retry with a fresh results ID.
    """
    validate_horizon(horizon)
    groups = list(_groups(run_id, data_root, alphabet_sizes))
    results_id = _results_id(results_id)
    outputs = [Path(data_root) / f"alphabet_{len(a.alphabet)}" / "cross_state" / run_id /
               results_id / f"states_{a.n_states}_vs_{b.n_states}" for a, b in groups]
    for out in outputs:
        for target in (out, out.with_name(out.name + ".part")):
            if target.exists():
                raise FileExistsError(f"refusing to overwrite {target}")
    return [_write_group(a, b, out, horizon, compress)
            for (a, b), out in zip(groups, outputs)]
