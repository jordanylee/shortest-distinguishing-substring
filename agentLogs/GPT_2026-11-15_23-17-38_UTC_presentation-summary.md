# Ten-figure presentation summary

Agent GPT; November 15, 2026, 23:17:38 UTC. User approved the detailed ten-figure plan before implementation. Read PROJECT_GUIDE.md first; consulted two parallel agents for independent numerical auditing and adversarial visual review.

## Deliverables

- Root `PRESENTATION_SUMMARY.md`: ten embedded 16:9 SVG figures, exact bucket tables, descriptive Pearson/Spearman correlations, within/cross comparison tables, brief captions, and a methods/provenance appendix.
- `dataviz/presentation_summary.py`: reproducible, read-only analysis of explicitly selected saved experiments. No DFAs generated and no comparisons recalculated.
- `dataviz/figures/presentation_summary/`: ten SVGs, four CSVs (`sds_buckets`, `correlations`, `similarity_bins`, `within_cross_comparison`), a validated aggregate cache, and input/script provenance.
- README, PROJECT_GUIDE, dataviz README, requirements (explicit NumPy dependency), and current-status links updated. Existing unrelated workspace changes and historical exports preserved.

## Scope and interpretation

Original source `2026-11-15_19-36-35-433280_UTC`, within result `2026-11-15_19-55-50-157162_UTC`, cross result `2026-11-15_21-03-45-337283_UTC`. High SDS source `2026-11-15_21-32-55-118406_UTC`, result `2026-11-15_21-33-59-533782_UTC`. All use saved H=5. Thirty-eight batches cover 6,243,500 pair rows.

Original distribution bars retain states 10/15/20/25/30; relationship figures use only 10/20/30 and cross combinations 10–20, 10–30, 20–30. High SDS bars use 5/10/15. Bars count exact lengths and separately display equivalent pairs; tail panels repeat longer buckets on an enlarged linear scale. Similarity curves retain finite SDS=0, exclude equivalents, use width-0.05 bins and observed mean x/y coordinates, break at empty bins, and flag n<30 with hollow points and faint dotted segments. Axes match within each alphabet across all relationship/overlay figures and metrics.

Overlay figures retain three separate translucent grey within-state curves. Their tables separately pool within/cross configurations and compare bins with at least 100 finite pairs in both pools, weighting absolute SDS-mean differences by the smaller count. Weighted differences are below 0.011 symbols across at least 99.85% of finite pairs, while some supported bins differ by about 0.336. Correlations use all finite pair observations with average ranks for ties; no independence-based significance claims.

Corrected the user's tentative maximum-length claim: alphabet 4 has four within-state SDS=3 pairs (10 states) and two cross-state SDS=3 pairs (10 vs 20). Alphabet 5 has none above 2. High SDS is an unfiltered separate seed-20 sample, not a selected subset.

## Validation and review

Ran `python -B dataviz/presentation_summary.py --preview-dir <temporary review directory>` for full validation and initial exports. Checked complete manifests, exact source/result/configuration IDs, source hashes, endpoint membership, unique/all-pair coverage, state-qualified cross endpoints, witness lengths/symbols, manifest histograms/equivalence counts, probability/weight ranges and identities, and necessary horizon constraints.

Verified average-rank ties against SciPy and bin boundary behavior at 0, 0.05, 0.999, and 1. Independent numerical agent recomputed all 24 relationship configurations and reconciled all 48 correlation rows (96 coefficients; maximum difference 1.11e-16), 304 bucket rows, 960 bin rows, and eight overlay rows. Original 480 bin rows exactly match earlier validated exports; cross pooled calculations independently scanned all three million cross rows. Markdown tables and tail claims matched independent expectations.

Adversarial agent inspected all ten individual PNG previews and a complete contact sheet, stored only under the system temporary directory. Fixed legend/panel-title overlaps, then received visual sign-off: exact tail/zero labels readable, grey references visible and subordinate, scales consistent, sparse bins disclosed. Also fixed inward rounding in strict prose bounds: bounds now round outward programmatically, while table values use ordinary rounding. Final exports rebuilt with `--reuse-validated`, rechecking every cached input hash.

Automated checks confirm ten vector-only SVGs with 16:9 view boxes, all summary links resolve, table widths are consistent, figure-level text stays within the canvas, and legends do not overlap panel titles. Final script hash is recorded in provenance. No outstanding implementation or review findings.
