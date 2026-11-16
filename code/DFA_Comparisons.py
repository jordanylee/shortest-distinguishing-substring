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
HORIZON = 3  # REQUIRED for similarity/both; set an integer >= 0. No research default chosen.
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

# %% [markdown]
# ## OPTIONAL: Compare different state sizes within each alphabet
#
# Compare **10 vs 20**, **10 vs 30**, and **20 vs 30** states, separately for each
# selected alphabet. States 15 and 25 are ignored, regardless of STATE_COUNTS.
# Each combination uses every DFA from one batch against every DFA from the
# other: 500 DFAs per batch gives 250,000 pairs per combination, 750,000 per
# alphabet (3,000,000 for four alphabets). Matching numeric DFA IDs across batches
# are distinct DFAs and are included. Reverse combinations are not repeated.
#
# This section computes SDS, agreement, and weighted Jaccard together, using the
# same bounded distribution as above. Set ENABLE_CROSS_STATE=True, choose the
# source run, alphabets, and horizon below, then run the preview/benchmark cell.
# Run the final cell when ready for the full computation. Leave the flag False
# to skip this section during Run All. Setup is required; earlier within-batch
# calculations do not need to be rerun. All three state batches must be present
# for each selected alphabet. The defaults below use the newer four-alphabet
# source run with H=5, matching its saved within-batch similarity results.
#
# Results are stored separately under
# `data/alphabet_<A>/cross_state/<source_run>/<results_id>/states_<S1>_vs_<S2>/`.
# Each directory has streamed pair records, DFA stats, and a provenance manifest.
# Existing results are never overwritten; after interruption, completed
# combinations remain valid and retries need a fresh CROSS_RESULTS_ID.
# Summaries keep equivalence separate from length zero. Comparisons sharing a
# DFA remain dependent observations, and these analyses are descriptive.
# The optional cells refresh their helper modules so an already-running kernel
# picks up code changes without rerunning the earlier experiments.

# %% Optional cross-state configuration
ENABLE_CROSS_STATE = True
CROSS_RUN_ID = "2026-11-15_19-36-35-433280_UTC"
CROSS_ALPHABET_SIZES = None  # All alphabets in CROSS_RUN_ID; optionally select a subset.
CROSS_HORIZON = 5  # Matches saved within-batch metrics for this source run.
CROSS_RESULTS_ID = None  # Fresh timestamp; independent of within-batch RESULTS_ID.

# %% Optional cross-state preview and benchmark (no files written)
if ENABLE_CROSS_STATE:
    import importlib
    import experiments
    import cross_state

    # Reload dependencies first: cross_state imports helpers from experiments.
    importlib.reload(experiments)
    importlib.reload(cross_state)

    cross_preview = cross_state.preview(CROSS_RUN_ID, DATA_ROOT, CROSS_ALPHABET_SIZES)
    for row in cross_preview:
        print(f"Alphabet {row['alphabet_size']}, states {row['state_count_a']} vs "
              f"{row['state_count_b']}: {row['dfa_count_a']:,} x {row['dfa_count_b']:,} "
              f"DFAs = {row['pair_count']:,} pairs")
    print(f"Total: {sum(row['pair_count'] for row in cross_preview):,} pairs; H={CROSS_HORIZON}")
    cross_timings = cross_state.benchmark(
        CROSS_RUN_ID, DATA_ROOT, horizon=CROSS_HORIZON,
        alphabet_sizes=CROSS_ALPHABET_SIZES, sample_pairs=BENCHMARK_PAIRS, seed=BENCHMARK_SEED)
    for row in cross_timings:
        print(f"Alphabet {row['alphabet_size']}, states {row['state_count_a']} vs "
              f"{row['state_count_b']}: {row['sample_pairs']} sampled pairs in "
              f"{row['sample_seconds']:.3f}s; estimated pair calculation "
              f"{row['estimated_pair_seconds'] / 60:.2f} min")
    print(f"Total estimate: {sum(row['estimated_pair_seconds'] for row in cross_timings) / 60:.2f} min "
          "(pair calculations only; stats, gzip, and disk I/O add time)")
else:
    print("Optional cross-state comparisons disabled. Set ENABLE_CROSS_STATE=True to enable.")

# %% Optional full cross-state run and saved-result summaries
if ENABLE_CROSS_STATE:
    import importlib
    import experiments
    import cross_state
    import result_summary

    importlib.reload(experiments)
    importlib.reload(cross_state)
    importlib.reload(result_summary)

    cross_result_dirs = cross_state.run_all(
        CROSS_RUN_ID, DATA_ROOT, horizon=CROSS_HORIZON, alphabet_sizes=CROSS_ALPHABET_SIZES,
        results_id=CROSS_RESULTS_ID, compress=COMPRESS_OUTPUT)
    print("Cross-state results ID:", cross_result_dirs[0].parent.name)
    for path in cross_result_dirs:
        print(path)
        report = result_summary.markdown_summary(result_summary.summarize(path))
        try:
            from IPython.display import Markdown, display
        except ImportError:
            print(report)
        else:
            display(Markdown(report))
