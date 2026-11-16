# Explain and plot SDS tail counts

Agent GPT; November 15, 2026, America/Chicago.

Implemented the requested tail-count plot in `dataviz/sds_tail_counts.py`, with parameter notebook `SDS_Tail_Counts.ipynb`. Updated visualization README and project status. Outputs are `dataviz/figures/sds_tail_counts/sds_tail_counts.svg`, exact CSV, and provenance.

The single SVG has alphabet-2 and alphabet-3 panels, five lines each for generated state counts 10/15/20/25/30. Thresholds 2–6 count all pairs with finite SDS at least that threshold, using matching logarithmic axes. Embedded instructions explain cumulative/nested counts, log tick spacing, omitted SDS 0/1, equivalent-pair exclusion, and zero counts. Exact tables below both panels avoid overlapping point labels and show every zero. Worked example: binary/10-state at threshold 4 includes 68 SDS=4 plus nine SDS=6 pairs, total 77.

Read and checked ten complete saved comparison manifest histograms from source `2026-11-15_19-36-35-433280_UTC`, results `2026-11-15_19-55-50-157162_UTC`; no raw pair calculations or generation. Ran script successfully. Checked CSV counts, cumulative monotonicity, zero ternary tails, 124,750-pair manifest denominators, SVG XML, input/script provenance hashes, notebook schema and code compilation. No repository tests added/run; notebook kernel was not executed. Preserved existing figures and unrelated workspace changes.
