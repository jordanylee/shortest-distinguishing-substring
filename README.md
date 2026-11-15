# Shortest Distinguishing String

## 1. Summary

We are answering the question: **For two non-equivalent DFAs, how long does the shortest string distinguishing their languages tend to be?** A distinguishing string is accepted by exactly one of the two deterministic finite automata (DFAs).

We will use DeepDFA to generate a large collection of DFAs, varying the number of states and alphabet size. An initial exploratory run will empirically measure the distribution of shortest distinguishing string lengths. We will then form a hypothesis based on these observations and run more tailored simulations to investigate it.

## 2. Guidelines

- Put time-sensitive information, including current project status and next steps, in [time-sensitive.md](time-sensitive.md).
- Store generated DFAs, result files, and data visualizations in `/data`.
- For every session, create a Markdown file in `/agentLogs`. Include the agent name (`GPT` or `Claude`), date, time, and basic project or purpose in the filename; for example, `GPT_2026-11-14_18-02-15_project-documentation.md`. Summarize the work performed with a focus on traceability: what changed, why, which files were affected, and any checks or outstanding work.
- Put code for running tests, experiments, and analysis in `/code`. DFA generation is handled through DeepDFA.

## 3. Run DFA comparisons

Open [code/DFA_Comparisons.ipynb](code/DFA_Comparisons.ipynb) with a Python 3.12 kernel, starting Jupyter from the repository root or `code/`. Edit the configuration cell, preview the selected batches, benchmark, and run. Choose `"sds"`, `"similarity"`, or `"both"`. Similarity requires an explicit nonnegative `HORIZON`; the notebook leaves it unset so an experimental horizon is not chosen implicitly.

The notebook and matching [Python companion](code/DFA_Comparisons.py) call importable modules for all calculations and storage. New results go under each batch's `comparisons/<results_id>/`; existing SDS-only `pairs/` outputs remain available. The final notebook cell summarizes SDS distributions, equivalent pairs, agreement, weighted Jaccard, and DFA sizes. See [similarity-metrics.md](similarity-metrics.md) for the metric definitions. Use a fresh kernel and Run All after configuring a final experiment.

Run checks with `python -m unittest discover -s code/tests -t code`. Calculation code uses the standard library. Fresh-kernel notebook tests additionally use `nbformat`, `nbclient`, and `ipykernel` and are skipped when these are unavailable.
