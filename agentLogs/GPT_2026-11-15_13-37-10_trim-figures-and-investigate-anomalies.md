# Trim figures and investigate H=4 findings

User requested removal of minimal-size, unreachable-fraction, tail-concentration, and horizon-change figures; removal of cumulative similarity panels; and checks of state-count stability, 10-state similarity anomalies, and agreement histogram oscillation.

## Changes

- `dataviz/analyze.py`: H=4-only loading and provenance; no H=3 dependency. Removed seven figures, leaving 13. Similarity distributions now contain two histograms. Mean SDS bars have four-decimal labels. Retained the readability changes from the preceding session.
- `dataviz/diagnostics.py`: exact integer agreement-bin assignment, original/corrected bin audit, exact-score counts, state-count comparison, Jaccard sensitivity checks, anomaly pair/DFA exports, leave-one-DFA-out checks, repeated-cohort summaries.
- `dataviz/DFA_Visualizations.ipynb`: H=4-only parameters and revised inspection tables; saved outputs remain cleared.
- `dataviz/README.md`, `FINDINGS.md`: revised scope and focused interpretations.
- `dataviz/outputs/2026-11-15_17-55-16-095569_UTC/`: regenerated retained PNG/SVG figures, report, tables, provenance. Removed only named retired figure files and obsolete tables inside the resolved dataviz output directory. Raw results were not modified.

## Findings

State-count means are close, not identical. Binary means range 0.633996-0.634669; ternary 0.561483-0.569218. Independent per-word fair acceptance is a useful idealized reference, predicting about 0.632843/0.562622 without a state-count parameter; it is not an exact finite-DFA model.

Agreement oscillation was largely an artifact of floating-point histogram boundaries on the exact n/80 binary score grid. Exact nominal-bin assignment changes 24 of 40 binary/30-state bins, by as much as 3.075 percentage points. Original and corrected counts are retained; raw scores were not changed.

Binary/10-state SDS=4: 40/68 pairs involve zero H=4 acceptance in one DFA. Excluding these pairs raises mean Jaccard from 0.2876 to 0.6986 (28 remaining pairs).

Ternary/10-state SDS=3: eight DFAs (227, 279, 313, 340, 350, 360, 364, 426) form all 28 internal pairs, averaging Jaccard 0.0981. Other 49 pairs average 0.6467. A separate read-only inspection enumerated all 121 strings through length 4 for each of these eight source DFAs; all reject every string through length 2. Per-length acceptance counts are documented in FINDINGS.md. No production pair calculations or generation were rerun.

## Checks

Completed the analysis after trimming, then regenerated after adding focused diagnostics. All six H=4 batches passed the existing manifest/count/metric checks. Verified 13 PNG/SVG pairs, no H=3 labels in SVG exports, 30 input hashes, matching analysis and diagnostic hashes, histogram count conservation at 124,750 per batch, and notebook schema/compiled cells. Visually inspected the corrected histogram and annotated mean bars. No statistical significance claim or independent-pair test was made.
