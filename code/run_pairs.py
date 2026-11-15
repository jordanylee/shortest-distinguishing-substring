# %% [markdown]
# # Shortest distinguishing strings: batch driver
#
# Runs every unordered within-batch pair for one generated run and writes results to
# `data/alphabet_<A>/states_<S>/<run_id>/pairs/<results_id>/`. All logic lives in the
# modules next to this file; see `code/IMPLEMENTATION_PLAN.md`.
#
# Produce final result sets from a fresh session (`python3.12 code/run_pairs.py`),
# not from a kernel with cells run out of order.

# %% Setup
import gzip
import json
import logging
import sys
from collections import Counter
from pathlib import Path

try:
    CODE_DIR = Path(__file__).resolve().parent
except NameError:  # interactive session without __file__
    CODE_DIR = Path.cwd() if (Path.cwd() / "pairs.py").exists() else Path.cwd() / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import pairs  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
DATA_ROOT = CODE_DIR.parent / "data"

# %% Config
RUN_ID = "2026-11-15_00-36-37-375402_UTC"  # canonical exploratory run; do NOT also run 2026-11-15_00-30-21-627385_UTC
RESULTS_ID = None       # None -> new UTC timestamp, shared by all batches
ALPHABET_SIZES = None   # e.g. [2] to restrict; None means all
STATE_COUNTS = None     # e.g. [10, 20]; None means all

# %% Run
outs = pairs.run_all(RUN_ID, DATA_ROOT, results_id=RESULTS_ID,
                     alphabet_sizes=ALPHABET_SIZES, state_counts=STATE_COUNTS)

# %% Quick checks (read-only)
for out in outs:
    m = json.loads((out / "manifest.json").read_text())
    opener = gzip.open if m["pairs_file"].endswith(".gz") else open
    hist: Counter = Counter()
    with opener(out / m["pairs_file"], "rt") as f:
        for line in f:
            hist[json.loads(line)["length"]] += 1
    n_pairs = sum(hist.values())
    n_eq = hist.pop(None, 0)
    print(f"\n{out.relative_to(DATA_ROOT)}")
    print(f"  pairs: {n_pairs} (expected {m['expected_pair_count']})")
    print(f"  equivalent: {n_eq} ({n_eq / n_pairs:.4%})")
    print(f"  length histogram: {dict(sorted(hist.items()))}")
    print(f"  max finite length: {max(hist) if hist else None}")
    print(f"  minimal sizes: {m['minimal_histogram']}")
    print(f"  reachable counts: {m['reachable_histogram']}")
    print(f"  elapsed: {m['elapsed_seconds']}s")
