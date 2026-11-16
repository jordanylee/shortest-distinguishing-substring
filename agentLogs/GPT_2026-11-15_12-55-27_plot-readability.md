# Improve plot labels and explanations

User requested a readability pass over all figures after discussing the meaning of the acceptance-per-DFA axes.

Updated `dataviz/analyze.py` and regenerated its 20 PNG/SVG figure pairs and report/provenance exports. Replaced ambiguous terms such as "finite partners" and "raw states" with explicit descriptions of non-equivalent comparisons and generated states. Clarified units, denominators, state minimization, acceptance percentages versus percentage-point differences, cumulative distributions, and matched score changes. Every exported figure now has explanatory footnotes. Display percentages use percentage ticks; integer lengths/counts use integer x ticks where applicable. CSV column names and calculations are retained.

Expanded figure space for footnotes, shortened the acceptance-per-DFA x label, gave mean-bar legends more space, and removed overlapping tail-count annotations (exact counts remain in CSV tables). Reviewed rendered figures across the distribution, acceptance, similarity, structure, and horizon-comparison views. Regeneration uses the same saved inputs and validation pipeline; no experiment calculations were rerun.
