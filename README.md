# Shortest Distinguishing String

Start with the [project guide](PROJECT_GUIDE.md) for a map of the notebooks, scripts, data, reports, and common workflows.

## 1. Summary

We are answering the question: **For two non-equivalent DFAs, how long does the shortest string distinguishing their languages tend to be?** A distinguishing string is accepted by exactly one of the two deterministic finite automata (DFAs).

We will use DeepDFA to generate a large collection of DFAs, varying the number of states and alphabet size. An initial exploratory run will empirically measure the distribution of shortest distinguishing string lengths. We will then form a hypothesis based on these observations and run more tailored simulations to investigate it.

## 2. Guidelines

- Put time-sensitive information, including current project status and next steps, in [time-sensitive.md](time-sensitive.md).
- Store generated DFAs, result files, and data visualizations in `/data`.
- For every session, create a Markdown file in `/agentLogs`. Include the agent name (`GPT` or `Claude`), date, time, and basic project or purpose in the filename; for example, `GPT_2026-11-14_18-02-15_project-documentation.md`. Summarize the work performed with a focus on traceability: what changed, why, which files were affected, and any checks or outstanding work.
- Put code for running tests, experiments, and analysis in `/code`. DFA generation is handled through DeepDFA.

## 3. Run DFA comparisons

Open [code/DFA_Comparisons.ipynb](code/DFA_Comparisons.ipynb) with a Python 3.12 kernel, starting Jupyter from the repository root or `code/`. Edit the configuration cell, preview the selected batches, benchmark, and run. Choose `"sds"`, `"similarity"`, or `"both"`. Similarity requires an explicit nonnegative `HORIZON`; select the horizon for your experiment in the configuration cell.

The notebook and matching [Python companion](code/DFA_Comparisons.py) call importable modules for all calculations and storage. New results go under each batch's `comparisons/<results_id>/`; existing SDS-only `pairs/` outputs remain available. The summary cells report SDS distributions, equivalent pairs, agreement, weighted Jaccard, and DFA sizes. See [similarity-metrics.md](similarity-metrics.md) for the metric definitions. Use a fresh kernel and Run All after configuring a final experiment.

The notebook ends with an **OPTIONAL** section for cross-state comparisons within each alphabet: 10 vs 20, 10 vs 30, and 20 vs 30 (15 and 25 are ignored). Set `ENABLE_CROSS_STATE=True`, inspect its preview and benchmark, then execute its final run/summary cell. Its separate configuration defaults to the four-alphabet source `2026-11-15_19-36-35-433280_UTC` and H=5, matching that source's saved within-batch metrics. At 500 DFAs per batch this adds 3,000,000 pairs across alphabets 2–5. It computes SDS, agreement, and weighted Jaccard, saving results under `data/alphabet_<A>/cross_state/<source_run>/<results_id>/states_<S1>_vs_<S2>/`. Earlier within-batch experiments do not need to be rerun; run the notebook configuration/setup and optional cells.

Run checks with `python -m unittest discover -s code/tests -t code`. Calculation code uses the standard library. Fresh-kernel notebook tests additionally use `nbformat`, `nbclient`, and `ipykernel` and are skipped when these are unavailable.

## 4. Compare the subset with fewer than half accepting states

[code/run_below_half.py](code/run_below_half.py) selects existing DFAs with **strictly fewer than 50% accepting states** for alphabets 2 and 3. It counts all raw generated states, including unreachable states. Both endpoints must pass the filter. Exactly 50% is excluded; zero accepting states is included. No DFAs are generated or modified, and source IDs are retained.

Preview the selected DFAs and unordered pair counts:

```powershell
python code/run_below_half.py
```

Compute SDS, agreement and weighted Jaccard for the selected within-batch pairs:

```powershell
python code/run_below_half.py --run --horizon 5
```

H=5 matches the current full-data comparisons. The script requires an explicit horizon for execution. Defaults use source `2026-11-15_19-36-35-433280_UTC` and generated state counts 10/15/20/25/30. Options: `--source-id`, `--data-root`, `--alphabets 2 3`, `--states 10 20 30`, and `--results-id`. Different sizes are kept in separate batches; there are no cross-size pairs.

Outputs go under each source batch's `comparisons_below_half/<results_id>/`, using the existing pair/stats/manifest format. A new timestamp is shared across selected batches by default. Existing results are never overwritten. Manifests record source count, selected IDs, per-DFA accepting counts and initial acceptance flags, the strict filter, horizon and code/input hashes. Empty or singleton subsets produce valid zero-pair outputs. Use `code/result_summary.py` to summarize a selected output directory.

This is a descriptive conditional analysis of the existing sample. Compare against the corresponding full batch at the same horizon, and remember that pairs share DFAs. Raw accepting-state fraction depends on representation and need not equal acceptance probability under the sampled word distribution.

## 5. Saved comparison tables

- [Below-50%-accepting subset](data/reports/below_half_accepting.md): selected counts, exact SDS distributions and comparisons with the full sample.
- [Additional seed-20 comparisons](data/reports/additional_comparisons_seed20.md): alphabets 2/3, state counts 5/10/15, exact SDS distributions and mean similarities.

Rebuild both Markdown reports from their explicitly selected saved results with `python code/write_comparison_tables.py`. This reads results only; it does not generate DFAs or rerun comparisons.

## 6. Presentation summary

[PRESENTATION_SUMMARY.md](PRESENTATION_SUMMARY.md) collects ten slide-sized SVG figures, exact SDS bucket tables, descriptive correlations, and within/cross-category curve comparisons. Rebuild it from the saved experiments with `python dataviz/presentation_summary.py`; see [dataviz/README.md](dataviz/README.md) for inputs, exports, and visual conventions.
