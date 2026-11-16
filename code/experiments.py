"""Notebook-independent orchestration for within-batch SDS and similarity runs."""

import hashlib
import json
import logging
import platform
import random
import re
import shutil
import time
from collections import Counter
from datetime import datetime, timezone
from dataclasses import replace
from itertools import combinations
from pathlib import Path

from dfa_stats import minimal_size, reachable_states
from distinguish import shortest_distinguishing
from loader import load_batch
from pairs import _JsonlWriter, _git_info, find_run_dirs, new_results_id
from similarity_metrics import METRIC_FIELDS, calculate_similarity, distribution, validate_horizon

log = logging.getLogger(__name__)


def validate_config(calculations, horizon):
    if calculations not in ("sds", "similarity", "both"):
        raise ValueError("calculations must be 'sds', 'similarity', or 'both'")
    if calculations != "sds":
        validate_horizon(horizon)


def _results_id(value):
    value = new_results_id() if value is None else value
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", value):
        raise ValueError("invalid results_id")
    return value


def select_batches(run_id, data_root, alphabet_sizes=None, state_counts=None):
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", run_id):
        raise ValueError("run_id must be a bare run identifier")
    dirs = find_run_dirs(run_id, data_root, alphabet_sizes, state_counts)
    if not dirs:
        raise FileNotFoundError(f"no batches selected for {run_id}")
    return dirs


def preview(run_id, data_root, alphabet_sizes=None, state_counts=None):
    """Validate selected batches and report their full unordered pair counts."""
    rows = []
    for path in select_batches(run_id, data_root, alphabet_sizes, state_counts):
        b = load_batch(path)
        n = len(b.dfas)
        rows.append({"run_dir": str(path), "alphabet_size": len(b.alphabet),
                     "state_count": b.n_states, "dfa_count": n, "pair_count": n * (n - 1) // 2})
    return rows


def _pair_record(a, b, alphabet, calculations, horizon, *, sort_ids=True):
    if sort_ids:
        a, b = sorted((a, b), key=lambda d: d.id)
    row = {"a": a.id, "b": b.id}
    if calculations != "similarity":
        result = shortest_distinguishing(a, b, len(alphabet), check=False)
        row.update(length=result.length, witness=None if result.witness is None else
                   [alphabet[s] for s in result.witness])
    if calculations != "sds":
        result = calculate_similarity(a, b, alphabet, horizon, check=False)
        row.update({key: float(result[key]) for key in METRIC_FIELDS})
    return row


def benchmark(run_id, data_root, *, calculations="both", horizon=None,
              alphabet_sizes=None, state_counts=None, sample_pairs=100, seed=42):
    """Time a reproducible uniform sample per batch; writes no results.

    Estimates cover pair calculations only, not stats, compression, or disk I/O.
    """
    validate_config(calculations, horizon)
    if type(sample_pairs) is not int or sample_pairs < 1:
        raise ValueError("sample_pairs must be a positive integer")
    rng = random.Random(seed)
    rows = []
    for path in select_batches(run_id, data_root, alphabet_sizes, state_counts):
        b = load_batch(path)
        n = len(b.dfas)
        total = n * (n - 1) // 2
        ranks = rng.sample(range(total), min(sample_pairs, total))
        chosen = []
        for rank in ranks:
            i = 0
            while rank >= n - i - 1:
                rank -= n - i - 1
                i += 1
            chosen.append((b.dfas[i], b.dfas[i + rank + 1]))
        started = time.perf_counter()
        for a, other in chosen:
            _pair_record(a, other, b.alphabet, calculations, horizon)
        elapsed = time.perf_counter() - started
        rows.append({"alphabet_size": len(b.alphabet), "state_count": b.n_states,
                     "sample_pairs": len(chosen), "sample_seconds": elapsed,
                     "estimated_pair_seconds": elapsed * total / len(chosen) if chosen else 0,
                     "seed": seed, "calculations": calculations, "horizon": horizon})
    return rows


def below_half_accepting(dfa):
    """Strict raw-state filter; exactly 50% is excluded, with no float rounding."""
    return 2 * sum(dfa.accept) < len(dfa.accept)


def run_batch(run_dir, *, calculations="both", horizon=None, results_id=None, compress=True,
              below_half_only=False):
    validate_config(calculations, horizon)
    results_id = _results_id(results_id)
    batch = load_batch(Path(run_dir))
    source_dfa_count = len(batch.dfas)
    selection_metadata = {}
    if below_half_only:
        batch = replace(batch, dfas=tuple(d for d in batch.dfas if below_half_accepting(d)))
        selection_metadata = {
            "source_dfa_count": source_dfa_count,
            "dfa_selection": {
                "name": "strictly_below_half_accepting",
                "predicate": "2 * accepting_state_count < raw_state_count",
                "state_basis": "all raw generated states, including unreachable states",
                "pair_rule": "both endpoints must satisfy the predicate; within-batch only",
                "selected_ids": sorted(d.id for d in batch.dfas),
                "excluded_dfa_count": source_dfa_count - len(batch.dfas),
                "selected_dfas": [{"id": d.id, "accepting_states": sum(d.accept),
                                   "raw_states": len(d.accept), "initial_accepting": d.accept[d.initial]}
                                  for d in sorted(batch.dfas, key=lambda d: d.id)]}}
    if calculations != "sds" and not batch.alphabet:
        raise ValueError("similarity requires a nonempty alphabet")
    out = batch.run_dir / ("comparisons_below_half" if below_half_only else "comparisons") / results_id
    part = out.with_name(results_id + ".part")
    for path in (out, part):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite {path}")
    part.mkdir(parents=True)
    started = datetime.now(timezone.utc)
    clock = time.perf_counter()
    suffix = ".jsonl.gz" if compress else ".jsonl"
    pair_name, stats_name = "pairs" + suffix, "dfa_stats" + suffix
    lengths, reachable, minimal = Counter(), Counter(), Counter()
    equivalent = 0
    count = 0
    try:
        with _JsonlWriter(part / stats_name, compress) as writer:
            for d in batch.dfas:
                r, m = len(reachable_states(d)), minimal_size(d, len(batch.alphabet))
                reachable[r] += 1
                minimal[m] += 1
                writer.write({"id": d.id, "n_states": len(d.delta), "reachable": r, "minimal": m})
        with _JsonlWriter(part / pair_name, compress) as writer:
            for a, b in combinations(batch.dfas, 2):
                row = _pair_record(a, b, batch.alphabet, calculations, horizon)
                writer.write(row)
                count += 1
                if "length" in row:
                    if row["length"] is None:
                        equivalent += 1
                    else:
                        lengths[row["length"]] += 1
                if count % 1000 == 0:
                    log.info("%s: %d pairs completed", batch.run_dir, count)
        manifest = {
            "schema_version": 1, "results_kind": "dfa_comparisons", "results_id": results_id,
            "source_run_id": batch.run_id, "source_run_dir": str(batch.run_dir.resolve()),
            "source_sha256": batch.input_sha256, "alphabet": list(batch.alphabet),
            "alphabet_size": len(batch.alphabet), "state_count": batch.n_states,
            "dfa_count": len(batch.dfas), "calculations": calculations,
            **selection_metadata,
            "pairing_scheme": "all unordered within-batch pairs, a<b by id",
            "pair_key": ["source_run_id", "alphabet_size", "state_count", "a", "b"],
            "expected_pair_count": len(batch.dfas) * (len(batch.dfas) - 1) // 2,
            "pair_count": count, "pairs_file": pair_name, "dfa_stats_file": stats_name,
            "pairs_layout": {"a": "smaller source DFA ID; weight_a refers to this DFA",
                             "b": "larger source DFA ID; weight_b refers to this DFA",
                             "length": "SDS symbol count; null if equivalent; absent in similarity-only mode",
                             "witness": "shortest witness in manifest alphabet order, as symbol tokens; null if equivalent",
                             "metrics": "agreement, weighted Jaccard, and five language weights; absent in SDS-only mode"},
            "dfa_stats_layout": {"id": "source DFA ID", "n_states": "raw state count",
                                 "reachable": "reachable state count", "minimal": "minimal complete DFA size"},
            "compression": "gzip" if compress else "none",
            "distribution": distribution(batch.alphabet, horizon) if calculations != "sds" else None,
            "interpretation": "descriptive; horizon was not preregistered before existing SDS results",
            "output_numbers": "metrics converted from exact rationals to binary64 floats",
            "equivalent_pair_count": equivalent if calculations != "similarity" else None,
            "length_histogram": dict(sorted(lengths.items())) if calculations != "similarity" else None,
            "reachable_histogram": dict(sorted(reachable.items())),
            "minimal_histogram": dict(sorted(minimal.items())),
            **_git_info(), "python_version": platform.python_version(),
            "code_sha256": {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                            for name in (("experiments.py", "similarity_metrics.py", "loader.py",
                                          "distinguish.py", "dfa_stats.py", "pairs.py") +
                                         (("run_below_half.py",) if below_half_only else ()))},
            "started_utc": started.isoformat(), "finished_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": time.perf_counter() - clock, "status": "complete"}
        (part / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        part.rename(out)
    except BaseException:
        shutil.rmtree(part, ignore_errors=True)
        raise
    log.info("Completed %s (%d pairs)", out, count)
    return out


def run_all(run_id, data_root, *, calculations="both", horizon=None, results_id=None,
            alphabet_sizes=None, state_counts=None, compress=True):
    validate_config(calculations, horizon)
    dirs = select_batches(run_id, data_root, alphabet_sizes, state_counts)
    results_id = _results_id(results_id)
    # Check all destinations before starting; completed batches remain valid if a later batch fails.
    for path in dirs:
        for name in (results_id, results_id + ".part"):
            target = path / "comparisons" / name
            if target.exists():
                raise FileExistsError(f"refusing to overwrite {target}")
    return [run_batch(path, calculations=calculations, horizon=horizon,
                      results_id=results_id, compress=compress) for path in dirs]
