# Curated DFA figures

All active scripts export **SVG only**, and notebooks display SVGs. The historical archive remains a snapshot of earlier work.

## Presentation summary

[PRESENTATION_SUMMARY.md](../PRESENTATION_SUMMARY.md) collects ten 16:9 SVG figures with exact tables and short captions: original SDS buckets (alphabets 2/3), in-category and cross-category similarity relationships (alphabets 2–5), cross-category curves with grey in-category references, and High SDS seed-20 buckets (alphabets 2/3).

Run `python dataviz/presentation_summary.py` from the root. The script validates all 6,243,500 saved pair rows across 38 explicitly selected complete batches, source hashes, endpoint identities, histograms, and score/weight consistency. It performs no new comparisons. Original distribution bars retain all five state sizes; similarity figures use only 10/20/30. Both metrics use saved H=5.

Exports live in [figures/presentation_summary/](figures/presentation_summary/): ten SVGs, `sds_buckets.csv`, `correlations.csv`, `similarity_bins.csv`, `within_cross_comparison.csv`, `validated_summary.json`, and `provenance.json`. Pearson/Spearman correlations use finite pair observations, including SDS 0; average ranks handle ties. Hollow markers and faint dotted segments flag bins with fewer than 30 pairs. Empty bins break lines. Overlay comparison tables separately pool within/cross configurations and compare bins with at least 100 finite pairs in both pools, weighting absolute SDS-mean differences by the smaller count. These tables describe common populated regions rather than asserting identical curves.

For styling-only changes, `--reuse-validated` reloads cached summaries after rechecking every input hash. `--preview-dir <path>` optionally writes temporary PNGs for visual review; the deliverable remains SVG. The inputs and exact IDs are documented in the root summary. No older plots or archived files are replaced by this workflow.

## State distributions

Two figures, each with twenty colored lines:

- [Reachable states](figures/reachable_states.svg)
- [Minimal states](figures/minimal_states.svg)

Alphabet sizes: 2, 3, 4, 5. Generated state counts: 10, 15, 20, 25, 30. Each line uses 500 DFAs; its percentages sum to 100%. Both figures use the same colors and legend. Lines connect the observed frequencies at integer state counts, including zero-frequency counts, up to each configuration's generated size.

Alphabet families use blue (2 symbols), red (3), green (4), and purple (5). Within each family, darker shades indicate more generated states, from 10 to 30.

Open [State_Distributions.ipynb](State_Distributions.ipynb) to edit parameters, generate, and display both figures. The implementation is in [state_distributions.py](state_distributions.py). From the repository root:

```powershell
python dataviz/state_distributions.py
```

The script reads saved per-DFA statistics from source run `2026-11-15_19-36-35-433280_UTC`, comparison run `2026-11-15_19-55-50-157162_UTC`. State statistics are independent of the similarity horizon; no pair scores are loaded. All twenty configurations must be complete and contain 500 matched source/stat records. Saved histograms and source hashes are checked before plotting.

SVG versions, one CSV of counts/percentages, and input provenance are saved in `figures/`. Repeating the script replaces these visualization exports. Python dependencies: matplotlib; opening the notebook additionally requires Jupyter/ipykernel.

## SDS tail counts

[View the tail-count plot](figures/sds_tail_counts/sds_tail_counts.svg). Two panels compare alphabets 2 and 3, with five generated state counts per panel. Open [SDS_Tail_Counts.ipynb](SDS_Tail_Counts.ipynb) or run `python dataviz/sds_tail_counts.py`.

At threshold **d**, the vertical value counts pairs with **finite SDS >= d**. It does not count only SDS exactly d. For example, binary/10-state at d=4 has 77 pairs: 68 with SDS=4, none with SDS=5, and 9 with SDS=6. Those 9 pairs are counted again at every smaller threshold. Do not add counts across thresholds.

The vertical axis is logarithmic: each major tick represents ten times the count below it. Zero counts cannot appear on this axis; they are explicitly shown in the exact-count tables beneath each panel. Lines stop when the count becomes zero. Both panels use identical axes. Thresholds start at 2 to focus on longer distinctions; SDS=0 and SDS=1 are omitted. Equivalent pairs have no finite SDS and are excluded.

The SVG includes these explanations and exact-count tables. The companion [CSV](figures/sds_tail_counts/sds_tail_counts.csv) contains all plotted thresholds and counts, including zeros; provenance records the ten saved input manifests. No pair calculations are rerun. These remain descriptive counts of pairs sharing DFAs.

## SDS versus similarity

Open [SDS_Similarity.ipynb](SDS_Similarity.ipynb), or run:

```powershell
python dataviz/sds_similarity.py
```

Four combined SVG files in `figures/sds_vs_similarity/`:

| Metric | By alphabet: four panels (2, 3, 4, 5) | By generated size: three panels (10, 20, 30) |
|---|---|---|
| Agreement | [SVG](figures/sds_vs_similarity/sds_vs_agreement_by_alphabets.svg) | [SVG](figures/sds_vs_similarity/sds_vs_agreement_by_states.svg) |
| Weighted Jaccard | [SVG](figures/sds_vs_similarity/sds_vs_jaccard_by_alphabets.svg) | [SVG](figures/sds_vs_similarity/sds_vs_jaccard_by_states.svg) |

Alphabet panels each have five state-count lines (10/15/20/25/30); state panels each have four alphabet lines. The original fourteen individual figures and their tables/provenance are preserved in `figures/sds_vs_similarity/individual/`. The script and notebook now produce and display only the four combined figures.

Similarity is on x. Each point shows **mean finite SDS** within a similarity bin of width 0.05; x is the observed mean similarity in that bin. Empty bins break lines. Bins are `[left,right)`, except the final bin includes 1. Change `BIN_COUNT` in the notebook or pass `--bins`. All plots share axis ranges. Colors match the state distributions above.

Equivalent pairs have no finite SDS and are excluded; zero-length distinctions are retained. Each configuration is summarized separately using every pair. Counts, SDS ranges, and means for every bin are in `figures/sds_vs_similarity/sds_similarity_bins.csv`. Batch denominators, equivalent counts, input hashes, and script hash are in `figures/sds_vs_similarity/sds_similarity_provenance.json`.

Uses the same source/comparison IDs as the state figures. Saved manifests specify **H=5**. No experiments are rerun. The loader streams scores and checks pair keys, source hashes, counts, SDS histograms, score ranges, and necessary horizon constraints. The script accepts `--source-id`, `--results-id`, and `--output`.

These are descriptive comparisons of pairs that share DFAs. At H=5, SDS d forces agreement >= min(d/6,1), and d>5 forces both bounded scores to one. Similarity cannot establish language equivalence. Sparse bins may have unstable means; inspect their counts before interpreting tails.

The previous visualization workspace, including code, notebook, figures, tables, and notes, is preserved in [the archive](../archive/dataviz_2026-11-15_14-30-09/). It is a historical snapshot; its scripts assume their original location in `dataviz/`.
