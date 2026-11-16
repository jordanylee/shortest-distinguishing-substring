# Project guide

This repository studies the shortest string accepted by exactly one of two deterministic finite automata (DFAs), and how that length relates to language similarity. The workflow is: generate DFAs, compare them, then summarize or plot saved results.

Use this file to find your way around. Use [time-sensitive.md](time-sensitive.md) for experiment IDs, completed runs, findings, and next steps. Configuration cells and saved manifests determine what a particular run actually used.

## Where to start

| I want to… | Open or run | What it does |
|---|---|---|
| Generate new DFAs | [data/DFA_Generator.ipynb](data/DFA_Generator.ipynb) | Choose alphabet sizes, state counts, sample count, and seed; save a new source run. |
| Compare DFAs with the same alphabet and state count | [code/DFA_Comparisons.ipynb](code/DFA_Comparisons.ipynb) | Preview, benchmark, calculate SDS and/or similarities, and summarize the results. |
| Compare different state counts within an alphabet | The **OPTIONAL** section at the end of that comparison notebook | Compare 10–20, 10–30, and 20–30 states; ignore 15 and 25. |
| Compare only DFAs with fewer than half accepting states | [code/run_below_half.py](code/run_below_half.py) | Preview or calculate within-batch pairs where both DFAs pass the strict filter. |
| See reachable/minimal state distributions | [dataviz/State_Distributions.ipynb](dataviz/State_Distributions.ipynb) | Read saved DFA statistics and produce two SVG figures. |
| See how SDS relates to agreement/Jaccard | [dataviz/SDS_Similarity.ipynb](dataviz/SDS_Similarity.ipynb) | Read saved pair results and produce four combined SVG figures. |
| Count pairs with unusually long SDS | [dataviz/SDS_Tail_Counts.ipynb](dataviz/SDS_Tail_Counts.ipynb) | Plot counts with finite SDS **at least** each threshold, with exact-count tables. |
| Read the filtered-sample comparison | [data/reports/below_half_accepting.md](data/reports/below_half_accepting.md) | Compare the filtered subset with its full-sample baseline. |
| Read the additional 5/10/15-state experiment | [data/reports/additional_comparisons_seed20.md](data/reports/additional_comparisons_seed20.md) | Tables for the separate seed-20 sample. |
| Browse existing figures | [dataviz/README.md](dataviz/README.md) | Figure links and instructions for interpreting them. |
| Prepare presentation slides | [PRESENTATION_SUMMARY.md](PRESENTATION_SUMMARY.md) | Ten slide-sized figures, exact bucket tables, correlations, and within/cross comparisons. |

Generating and comparing create experimental data. Plotting and report scripts read saved experiments; they do not recalculate the pairs.

## What the folders contain

| Folder | Purpose |
|---|---|
| [code/](code/) | Comparison algorithms, experiment runners, result summaries, report generation, and tests. |
| [data/](data/) | The generator notebook/script, generated DFA batches, saved comparison results, and Markdown reports. |
| [dataviz/](dataviz/) | Active visualization notebooks, plotting scripts, and exported figures/tables. This is the established plotting location despite the older general convention to put analysis in `code/` and plots in `data/`. |
| [DeepDFA/](DeepDFA/) | Third-party Git submodule. This project uses its random-DFA generator. Its neural-learning experiments are separate from this project's comparison workflow. |
| [archive/](archive/) | The previous visualization workspace, preserved as a historical snapshot. |
| [agentLogs/](agentLogs/) | Session-by-session records of changes, reasoning, validation, and outstanding work. |

## Notebooks and scripts you run

The generator and comparison notebooks have corresponding `# %%` Python files. The plotting notebooks call separate plotting modules. Check the configuration in the file you are actually running: notebook and Python-file settings are saved separately and can differ.

| File | Role and behavior |
|---|---|
| [data/DFA_Generator.py](data/DFA_Generator.py) | Python companion to the generator notebook. Imports `DeepDFA/Random_DFA.py`, assigns reproducible seeds, validates records, and writes batches/manifests. Running the file generates data. |
| [code/DFA_Comparisons.py](code/DFA_Comparisons.py) | Python companion to the comparison notebook, including the optional cross-state section. Running the whole file executes enabled experiment cells. |
| [code/run_below_half.py](code/run_below_half.py) | Command-line runner for alphabets 2/3. Keeps DFAs with strictly fewer than 50% accepting **raw** states, including unreachable states. Exactly 50% is excluded. Defaults include state counts 10/15/20/25/30; no cross-state pairs. Without `--run`, it only previews. |
| [code/write_comparison_tables.py](code/write_comparison_tables.py) | Regenerates the two Markdown reports in `data/reports/` from explicit source/result IDs stored in the script. Checks saved counts, source hashes, and matching H=5. This is a report for particular experiments; edit its constants to change the inputs. |
| [code/run_pairs.py](code/run_pairs.py) | Original SDS-only driver. Writes to `pairs/`. Still available for that workflow; the combined comparison notebook also supports SDS-only calculations. |
| [dataviz/state_distributions.py](dataviz/state_distributions.py) | Implements the state-distribution notebook. Reads saved per-DFA statistics, validates them against sources, and writes two SVGs, `state_distributions.csv`, and `provenance.json` in `dataviz/figures/`. |
| [dataviz/sds_similarity.py](dataviz/sds_similarity.py) | Implements the SDS/similarity notebook. Bins similarity scores and plots mean finite SDS per bin. Writes four SVGs plus bin counts and provenance in `dataviz/figures/sds_vs_similarity/`. |
| [dataviz/sds_tail_counts.py](dataviz/sds_tail_counts.py) | Implements the SDS-tail notebook. Reads saved length histograms for alphabets 2/3 and writes an SVG, exact-count CSV, and provenance in `dataviz/figures/sds_tail_counts/`. |
| [dataviz/presentation_summary.py](dataviz/presentation_summary.py) | Validates 38 explicitly selected saved comparison batches from the original within/cross-state and seed-20 High SDS runs. Exports ten 16:9 SVGs, bucket/correlation/bin/comparison CSVs, cached summaries and provenance to `dataviz/figures/presentation_summary/`, and writes `PRESENTATION_SUMMARY.md` in the root. Reads saved data only. |

The active plots select saved **within-batch** comparisons. Their state-count panels compare summaries from those batches; they do not load the optional cross-state experiment results. The state and similarity scripts also share configuration/colors through `state_distributions.py`.

## Calculation modules behind the notebooks

These are imported helpers. Usually you edit parameters in a notebook or runner rather than running these files directly.

| Module | Responsibility |
|---|---|
| [code/loader.py](code/loader.py) | Defines the `DFA` and `Batch` records. Loads one source batch, validates its manifest/transitions/IDs, handles plain or gzip JSONL, and hashes source files. |
| [code/distinguish.py](code/distinguish.py) | Breadth-first search through pairs of DFA states. Returns the shortest distinguishing length and witness, or equivalence if no distinguishing string exists. It follows the manifest's symbol order to choose among shortest witnesses. |
| [code/dfa_stats.py](code/dfa_stats.py) | Counts reachable states and computes minimal complete DFA size. These measurements do not alter the saved source DFAs. |
| [code/similarity_metrics.py](code/similarity_metrics.py) | Computes agreement, weighted Jaccard, and language weights under the selected horizon. Uses exact integer/rational calculations before runners convert saved scores to floats. |
| [code/experiments.py](code/experiments.py) | Selects batches, previews pair counts, benchmarks samples, runs within-batch comparisons, writes result files/manifests, and supports the below-half selection. |
| [code/cross_state.py](code/cross_state.py) | Runs every DFA in one state-count batch against every DFA in another, for 10–20/10–30/20–30 within an alphabet. Saves distinct cross-state results and records each endpoint's state count. |
| [code/result_summary.py](code/result_summary.py) | Reads one explicitly selected saved result directory. Computes distributions, equivalence counts, mean similarities, and summaries by SDS length; formats Markdown tables. |
| [code/pairs.py](code/pairs.py) | Original SDS-only batch runner and storage format. Also supplies shared JSONL writing, run-directory discovery, result IDs, and Git provenance helpers to newer runners. |

## How to read the data folders

```text
data/
  DFA_Generator.ipynb / DFA_Generator.py
  alphabet_<A>/
    states_<S>/
      <source_run_id>/
        manifest.json
        <batch_file>.jsonl[.gz]
        comparisons/<results_id>/             # SDS, similarity, or both
        comparisons_below_half/<results_id>/  # filtered within-batch pairs
        pairs/<results_id>/                   # original SDS-only outputs
    cross_state/<source_run_id>/<results_id>/
      states_10_vs_20/
      states_10_vs_30/
      states_20_vs_30/
  reports/
    below_half_accepting.md
    additional_comparisons_seed20.md
```

**A source run** identifies generated DFAs. **A batch** is one source run, alphabet size, and generated state count. **A results ID** identifies a later calculation on those DFAs. One source can have several result sets, including different similarity horizons. The IDs need not match.

Read a source manifest to find the actual `batch_file`. Each JSONL line is a DFA: its ID, seed, initial state, transition table, and acceptance flags. `.gz` means compressed JSONL. Transition columns correspond to the explicit symbol list in the manifest.

Each completed comparison directory contains:

| File | Meaning |
|---|---|
| `manifest.json` | Inputs, calculation mode, similarity distribution/horizon where applicable, counts/histograms, hashes, timing, and completion status. |
| `pairs.jsonl` or `pairs.jsonl.gz` | One row per compared pair. SDS outputs contain `length` and `witness`; similarity outputs contain agreement/Jaccard and language weights. |
| `dfa_stats.jsonl` or `dfa_stats.jsonl.gz` | Per-DFA raw, reachable, and minimal state counts. |

An ID such as `0` is only unique within its source batch. Cross-state pairs can legitimately have `a == b` numerically because their state counts differ. Include source run, alphabet, and state count when identifying a DFA across batches.

Only completed manifests represent usable finished results. `.part` directories are temporary outputs. Experiment runners protect existing result directories; select a fresh results ID for another calculation. Select explicit IDs when analyzing results so multiple runs are not pooled accidentally.

## Common workflows

Run terminal examples from the repository root. Use Python 3.12 for the comparison workflow. Its calculation code uses the standard library. Notebooks need Jupyter/a Python kernel; plots use the packages in [dataviz/requirements.txt](dataviz/requirements.txt).

**Generate and compare:** open the generator notebook and inspect its configuration before running it. Record its source run ID. In the comparison notebook, set `RUN_ID`, alphabet/state selections, `CALCULATIONS`, and `HORIZON`; then preview, benchmark, run, and inspect results.

**Compare different state counts:** run the comparison notebook's configuration/setup cells, then configure its final OPTIONAL section. `CROSS_RUN_ID`, `CROSS_ALPHABET_SIZES`, and `CROSS_HORIZON` are separate from the earlier settings. Set `ENABLE_CROSS_STATE=True`, preview/benchmark, then run its final cell. Each selected alphabet requires all three source batches. With 500 DFAs in each batch, this produces 250,000 pairs per state combination, or 750,000 per alphabet. Check the enable flag before using Run All.

**Preview the below-half subset; then calculate if desired:**

```powershell
python code/run_below_half.py
python code/run_below_half.py --run --horizon 5
```

Use its `--source-id`, `--alphabets`, and `--states` options to select inputs. H=5 matches the full-data run used by the existing reports; compare scores at a consistent horizon.

**Regenerate figures from saved comparisons:**

```powershell
python dataviz/state_distributions.py
python dataviz/sds_similarity.py
python dataviz/sds_tail_counts.py
```

Each accepts `--source-id`, `--results-id`, and `--output`. The similarity script also accepts `--bins`. Their default saved runs/configuration selections are defined in the plotting code; creating a new experiment does not automatically select it for plotting. The state and similarity workflows expect the twenty alphabet/state configurations described in [dataviz/README.md](dataviz/README.md).

**Regenerate the experiment-specific Markdown reports:**

```powershell
python code/write_comparison_tables.py
```

Plotting and report generation replace their exports at the selected destinations. Experimental source/result files remain the inputs.

## Terms that affect interpretation

| Term | Meaning here |
|---|---|
| SDS | Shortest distinguishing **string**: a word accepted by exactly one DFA. Length counts symbol tokens, not characters in symbol labels. |
| SDS length 0 | The empty string distinguishes the pair. This is a finite distinction. |
| Equivalent pair | No string distinguishes the languages. Saved SDS length/witness are `null`, not zero. |
| Generated/raw states | The state count requested from the generator, including unreachable states. |
| Reachable states | States accessible from the initial state. |
| Minimal states | Size of the smallest complete DFA recognizing the same language. |
| Horizon H | Similarity samples a length uniformly from 0 through H, then samples symbols uniformly. It does not weight every word across all lengths equally. |
| Agreement | Probability that both DFAs give the same answer, including joint rejection. |
| Weighted Jaccard | Accepted-language intersection weight divided by union weight; defined as 1 when the union weight is zero. |
| SDS tail count at d | Number of pairs with finite SDS at least d. Counts at different thresholds overlap. |

A bounded similarity score of 1 does not prove language equivalence. Raw accepting-state fraction is different from the probability of accepting a sampled word. Pairs sharing a DFA are dependent observations, and DeepDFA's generator is not uniform sampling over all DFAs. Metric definitions and original design decisions are in [similarity-metrics.md](similarity-metrics.md).

## Tests, documentation, and historical files

Run the test suite from the repository root:

```powershell
python -B -m unittest discover -s code/tests -t code
```

| Test files | What they cover |
|---|---|
| [test_loader.py](code/tests/test_loader.py), [test_distinguish.py](code/tests/test_distinguish.py), [test_dfa_stats.py](code/tests/test_dfa_stats.py) | Source validation, shortest witnesses/equivalence, and reachable/minimal sizes. |
| [test_similarity_metrics.py](code/tests/test_similarity_metrics.py) | Metric calculations, distribution semantics, and edge cases. |
| [test_pairs.py](code/tests/test_pairs.py), [test_experiments.py](code/tests/test_experiments.py) | Pair generation, storage, modes, manifests, and summaries. |
| [test_cross_state.py](code/tests/test_cross_state.py), [test_below_half.py](code/tests/test_below_half.py) | Cross-batch identities/completeness and strict filter boundaries. |
| [test_comparison_notebook.py](code/tests/test_comparison_notebook.py) | Notebook/companion synchronization, fresh-kernel runs, and cached-import regression. Kernel checks require `nbformat`, `nbclient`, and `ipykernel`. |
| [test_real_data.py](code/tests/test_real_data.py) | Checks against particular historical datasets. Availability of those source runs matters. |
| [helpers.py](code/tests/helpers.py), [__init__.py](code/tests/__init__.py) | Synthetic DFAs, brute-force oracles, temporary batch writing, and test-package setup. |

The modules in `code/` are sibling imports, not a package named `code` (which would conflict with Python's standard-library module). The test command above arranges the import path.

| Document or location | When to read it |
|---|---|
| [README.md](README.md) | Project overview, conventions, and main execution instructions. |
| [time-sensitive.md](time-sensitive.md) | Current run IDs, completed work, observations, and next steps. Later updates can supersede older entries. |
| [similarity-metrics.md](similarity-metrics.md) | Metric formulas, distribution, implementation requirements, and original design history. |
| [code/IMPLEMENTATION_PLAN.md](code/IMPLEMENTATION_PLAN.md) | Original SDS algorithm/storage design. Its scope is the initial within-batch implementation. |
| [code/REVIEW_FIXES.md](code/REVIEW_FIXES.md) | Historical code-review findings and their resolutions. |
| [dataviz/README.md](dataviz/README.md) | Active figure gallery, plot meanings, input expectations, and export behavior. |
| [CLAUDE.md](CLAUDE.md) | Instructions and project background for Claude Code. Some setup/status statements are historical. |
| [archive/README.md](archive/README.md) | Explains the archived visualization snapshot and its file-hash inventory. |
| [archive/dataviz_2026-11-15_14-30-09/](archive/dataviz_2026-11-15_14-30-09/) | Old `DFA_Visualizations.ipynb`, `analyze.py`, `diagnostics.py`, findings, reports, plots, and tables. Its scripts assumed their original location; use `dataviz/` for active plotting. |
| [dataviz/figures/sds_vs_similarity/individual/](dataviz/figures/sds_vs_similarity/individual/) | Earlier individual SVGs and supporting exports retained when the four combined figures replaced them. |
| [agentLogs/](agentLogs/) | Detailed change history and verification evidence by session. |
| [.gitmodules](.gitmodules), [.gitignore](.gitignore) | DeepDFA submodule configuration, and exclusions for caches/temporary output. `.git/` holds version-control metadata; `__pycache__/` holds generated Python caches. |

Within [DeepDFA/](DeepDFA/), `Random_DFA.py` is the generator used here. `create_dfa.py` contains upstream DFA constructors; `DeepAutoma.py` and `Neural_DFA_identification.py` implement neural-learning machinery; `do_experiments.py`, `test_methods.py`, and `utils.py` support upstream experiments. Its `datasets_*` and `random_DFAs` folders belong to those experiments. See [DeepDFA/README.md](DeepDFA/README.md) for that separate workflow. Generating this project's random DFAs does not require the upstream neural-training dependencies.

When adding a script or notebook, add its purpose, inputs, and output destination to this guide. Keep dated experiment results in `time-sensitive.md` or `data/reports/`, and link detailed plotting instructions from `dataviz/README.md`.
