# %% [markdown]
# # DFA comparisons: SDS and language similarity
#
# Edit the configuration cell, inspect the preview and benchmark, then run the
# full-experiment cell. All calculations and file handling live in sibling modules.
# Requires Python 3.12 and a Jupyter Python kernel; calculation modules use only
# the standard library. Start Jupyter from the repository root or `code/`.
#
# SDS is the shortest word accepted by exactly one DFA. Similarity samples length
# uniformly from 0 through H, then samples symbols independently and uniformly.
# Agreement includes jointly rejected words; weighted Jaccard compares accepted
# words. A score of 1 through H does not establish language equivalence.
#
# Existing canonical SDS results have already been examined. Similarities on
# these data are descriptive. Pairs sharing a DFA are dependent observations.
# See `../similarity-metrics.md` for the definitions and validation requirements.

# %% Configuration
RUN_ID = "2026-11-15_00-36-37-375402_UTC"
ALPHABET_SIZES = [2, 3]  # None selects all alphabet sizes.
STATE_COUNTS = [10, 20, 30]  # None selects all state counts.
CALCULATIONS = "both"  # "sds", "similarity", or "both".
HORIZON = None  # REQUIRED for similarity/both; set an integer >= 0. No research default chosen.
RESULTS_ID = None  # None creates a fresh UTC timestamp shared by the selected batches.
COMPRESS_OUTPUT = True
BENCHMARK_PAIRS = 100  # Uniformly sampled pairs PER batch; no result files written.
BENCHMARK_SEED = 42
DATA_ROOT_OVERRIDE = None  # Optional Path/string for another data directory.

# %% Setup
import json
import logging
import sys
from pathlib import Path

search_root = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
if (search_root / "experiments.py").is_file():
    CODE_DIR = search_root
elif (search_root / "code" / "experiments.py").is_file():
    CODE_DIR = search_root / "code"
else:
    raise RuntimeError("Start this notebook from the repository root or code/ directory")
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import experiments
from result_summary import markdown_summary, summarize

DATA_ROOT = Path(DATA_ROOT_OVERRIDE) if DATA_ROOT_OVERRIDE is not None else CODE_DIR.parent / "data"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# %% [markdown]
# ## Preview the selected data
#
# Each batch is one alphabet size and one raw state count. Only unordered pairs
# within that batch are compared. Self-pairs and reversed duplicates are excluded.
# The older `2026-11-15_00-30-21-627385_UTC` run duplicates the canonical samples;
# do not combine the two as independent data. No new DFAs are generated here.

# %% Preview
selected_batches = experiments.preview(RUN_ID, DATA_ROOT, ALPHABET_SIZES, STATE_COUNTS)
for batch in selected_batches:
    print(f"Alphabet {batch['alphabet_size']}, states {batch['state_count']}: "
          f"{batch['dfa_count']:,} DFAs, {batch['pair_count']:,} pairs")
print(f"Total: {sum(b['pair_count'] for b in selected_batches):,} pairs")
print(f"Calculations: {CALCULATIONS}; horizon: {HORIZON}")

# %% [markdown]
# ## Benchmark before running all pairs
#
# Set HORIZON above before this cell if similarity is enabled. The benchmark uses
# a reproducible uniform sample from each selected batch, and writes no files.
# Estimates cover pair calculations only; statistics, gzip and disk I/O add time.
# Runtime can grow substantially with H, alphabet size and reachable product size.

# %% Benchmark
timings = experiments.benchmark(
    RUN_ID, DATA_ROOT, calculations=CALCULATIONS, horizon=HORIZON,
    alphabet_sizes=ALPHABET_SIZES, state_counts=STATE_COUNTS,
    sample_pairs=BENCHMARK_PAIRS, seed=BENCHMARK_SEED)
for timing in timings:
    print(f"Alphabet {timing['alphabet_size']}, states {timing['state_count']}: "
          f"{timing['sample_pairs']} sampled pairs in {timing['sample_seconds']:.3f}s; "
          f"estimated full pair calculation {timing['estimated_pair_seconds']:.1f}s")
print(f"Total estimated pair calculation: {sum(t['estimated_pair_seconds'] for t in timings):.1f}s")

# %% [markdown]
# ## Run the full experiment
#
# This cell writes new results under each source batch's
# `comparisons/<results_id>/`. Existing results are never overwritten. A failed
# batch removes its temporary output; earlier completed batches remain valid.
# To retry a failed multi-batch experiment, use a fresh results ID and inspect only
# that ID. Existing `pairs/` canonical SDS results are preserved.
#
# Use Restart Kernel and Run All for a reproducible final run after setting H.
# Re-executing the run cell with RESULTS_ID=None creates another result set.

# %% Run
result_dirs = experiments.run_all(
    RUN_ID, DATA_ROOT, calculations=CALCULATIONS, horizon=HORIZON,
    results_id=RESULTS_ID, alphabet_sizes=ALPHABET_SIZES,
    state_counts=STATE_COUNTS, compress=COMPRESS_OUTPUT)
print("Results ID:", result_dirs[0].name)
for result_dir in result_dirs:
    print(result_dir)

# %% [markdown]
# ## Inspect saved results
#
# Summaries read exactly the directories returned by this run. To inspect a prior
# run without calculating again, skip the Run cell and set result_dirs explicitly:
#
#     result_dirs = [DATA_ROOT / "alphabet_2" / "states_10" / RUN_ID /
#                    "comparisons" / "YOUR_RESULTS_ID"]
#
# For legacy SDS results, use `pairs` instead of `comparisons`. Summary helpers
# also understand the existing canonical SDS format. Equivalent pairs remain
# separate from length zero. Positive-length frequencies are conditional on L>0.

# %% Summaries
summaries = [summarize(path) for path in result_dirs]
for summary in summaries:
    report = markdown_summary(summary)
    try:
        from IPython.display import Markdown, display
    except ImportError:
        print(report)
    else:
        display(Markdown(report))
