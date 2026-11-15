# DFA exploratory data visualization

November 15, 2026, America/Chicago. Agent: GPT.

## Scope and files

Read the temporary visualization handoff, README, project guidance, similarity specification, status, and saved manifests. Used the user's requested `dataviz/` destination for code, notebook, and artifacts, overriding the usual code/data placement for this task.

- `dataviz/analyze.py`: read-only loading, provenance/configuration checks, scoped joins, matched H=3/H=4 analysis, 20 figures, CSV exports, report and provenance metadata.
- `dataviz/DFA_Visualizations.ipynb`: parameter cell, script invocation, report/figure display, anomaly inspection. Notebook outputs remain cleared.
- `dataviz/requirements.txt`, `README.md`, `FINDINGS.md`: dependencies, usage, interpretations and follow-up leads.
- `dataviz/outputs/2026-11-15_17-55-16-095569_UTC/`: 20 PNG/SVG figure pairs, CSV tables, report/gallery, provenance with input and script hashes.
- `time-sensitive.md`: recorded the visualization deliverable and corrected stale similarity-run status via a superseding update.

The selected source is `2026-11-15_00-36-37-375402_UTC`; H=4 results `2026-11-15_17-55-16-095569_UTC`; H=3 results `2026-11-15_17-35-18-493520_UTC`. Each horizon has 748,500 pairs across six batches and 3,000 source DFAs. No generation, SDS, or similarity calculations were rerun. Existing staged H=4 data and dirty DeepDFA state were preserved.

## Checks and interpretation

Executed the complete analysis, then reran after widening the paired Jaccard change histogram to its full possible range and expanding input hashing. All runs completed. Validation checks manifests, counts, unique complete unordered pair keys, scoped source/stat IDs, metric ranges/identities, necessary SDS agreement bounds, and matching SDS/stats across horizons. Independently checked exported batch denominators, paired-change classifications, figure counts, 48 input hashes, and current script hash. Validated notebook schema and compiled all code cells; did not execute the entire notebook in a kernel. Visually inspected SDS-versus-agreement, six SDS distributions, joint similarity density, and the initial matched-horizon figure. No repository test files were added or changed.

All nine binary/10-state SDS=6 pairs share DFA 458; its partners have minimal size 1 and recognize the empty language. Ten inequivalent pairs remain bounded-identical at H=4, versus 97 at H=3. These results are descriptive; shared DFA dependence, generator bias, horizon constraints, and sparse bins are documented. Accepting-state fractions are analyzed using pair mean, pair absolute difference, and a per-DFA partner-average view.

Outstanding: new independent batches or structural investigation of DFA 458 would be follow-up work, not part of this visualization run.
