"""Test helpers: DFA builders, brute-force oracle and a synthetic batch writer."""

from __future__ import annotations

import gzip
import itertools
import json
import random
from pathlib import Path

from loader import DFA


def make_dfa(delta, accept, id=0, initial=0) -> DFA:
    return DFA(id=id, delta=tuple(tuple(r) for r in delta), accept=tuple(bool(x) for x in accept),
               initial=initial)


def random_dfa(rng: random.Random, n: int, k: int, id=0) -> DFA:
    return make_dfa([[rng.randrange(n) for _ in range(k)] for _ in range(n)],
                    [rng.random() < 0.5 for _ in range(n)], id=id)


def run(d: DFA, word, start=None) -> bool:
    p = d.initial if start is None else start
    for s in word:
        p = d.delta[p][s]
    return d.accept[p]


def brute_force(a: DFA, b: DFA, k: int, max_len: int, p0=None, q0=None):
    """First disagreeing word in shortlex order up to max_len, or None."""
    for L in range(max_len + 1):
        for word in itertools.product(range(k), repeat=L):
            if run(a, word, p0) != run(b, word, q0):
                return word
    return None


def write_synthetic_batch(run_dir: Path, dfas, alphabet, compress=False, run_id="test-run",
                          manifest_overrides=None, drop_manifest_fields=()) -> Path:
    """Write a manifest and batch file in the generator's format (schema_version 1)."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    n_states = len(dfas[0].delta) if dfas else 1
    batch_file = f"dfas_alphabet-{len(alphabet)}_states-{n_states}_count-{len(dfas)}_{run_id}.jsonl"
    if compress:
        batch_file += ".gz"
    lines = [json.dumps({"id": d.id, "seed": "0", "initial_state": d.initial,
                         "transitions": [list(r) for r in d.delta],
                         "acceptance": list(d.accept)}, separators=(",", ":"))
             for d in dfas]
    data = ("\n".join(lines) + "\n").encode("utf-8")
    (run_dir / batch_file).write_bytes(gzip.compress(data) if compress else data)
    manifest = {
        "schema_version": 1,
        "status": "complete",
        "run_id": run_id,
        "state_count": n_states,
        "alphabet_size": len(alphabet),
        "alphabet": list(alphabet),
        "sample_count": len(dfas),
        "initial_state": 0,
        "batch_file": batch_file,
        "compression": "gzip" if compress else "none",
    }
    manifest.update(manifest_overrides or {})
    for field in drop_manifest_fields:
        manifest.pop(field, None)
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return run_dir


def write_raw_batch(run_dir: Path, records, alphabet, n_states, sample_count=None) -> Path:
    """Write arbitrary (possibly invalid) record dicts with a valid manifest."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    batch_file = "batch.jsonl"
    (run_dir / batch_file).write_text("".join(json.dumps(r) + "\n" for r in records))
    (run_dir / "manifest.json").write_text(json.dumps({
        "schema_version": 1, "status": "complete", "run_id": "raw", "state_count": n_states,
        "alphabet_size": len(alphabet), "alphabet": list(alphabet),
        "sample_count": len(records) if sample_count is None else sample_count,
        "initial_state": 0, "batch_file": batch_file}))
    return run_dir
