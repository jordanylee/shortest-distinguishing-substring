# Cross-state-size comparisons

Each state-size pair compares every DFA in one batch with every DFA in the other. Only 10, 20, and 30 states are included.

## Main observations

| Comparison | Observed result |
|---|---|
| Cross-state vs same-state comparisons | Pooled by alphabet, the positive mean SDS changes by less than **0.003 symbols**; mean agreement changes by less than **0.023 percentage points**, and mean Jaccard by less than **0.041 percentage points**. |
| Different state-size pairs within an alphabet | Positive mean SDS differs by less than **0.005 symbols** across the three combinations. There is no consistent increase as the state-size pair grows. |
| Increasing alphabet size | Pooled positive mean SDS falls from **1.2700** at alphabet 2 to **1.0314** at alphabet 5. Counts with SDS ≥3 fall from **6,575 to 0**, with 750,000 pairs per alphabet. |
| Longest distinctions | Just **4 pairs** have SDS=5, all at alphabet 2, states 10 vs 20. No cross-state pair has SDS above 5 or equivalent languages. |

## Experiment

| Setting | Value |
|---|---|
| Alphabets | 2, 3, 4, 5 symbols |
| State-size pairs | 10 vs 20; 10 vs 30; 20 vs 30 |
| DFAs per source batch | 500; 6,000 distinct source records across 12 batches |
| Pairs | 250,000 per combination; 750,000 per alphabet; **3,000,000 total** |
| Equivalent cross-state pairs | **0** |
| Similarity distribution | H=5; uniform length 0–5, then independent uniform symbols |

## Overview by alphabet

Pooled across the three cross-state combinations. Means include SDS=0 unless marked positive. Positive means use only finite SDS > 0.

| Alphabet | SDS 0–1 (% of all) | Mean SDS | Mean positive SDS | SDS ≥3 (count) | Maximum SDS | Mean agreement | Mean Jaccard |
|---|---|---|---|---|---|---|---|
| 2 | 87.378% | 0.6356 | 1.2700 | 6,575 | 5 | 50.018% | 31.068% |
| 3 | 93.676% | 0.5629 | 1.1271 | 175 | 3 | 49.984% | 31.915% |
| 4 | 96.722% | 0.5327 | 1.0656 | 2 | 3 | 49.993% | 32.172% |
| 5 | 98.429% | 0.5158 | 1.0314 | 0 | 2 | 49.993% | 32.349% |

## SDS by state-size pair

SDS=0 means the empty string distinguishes the pair. The tail percentage below uses **positive-SDS pairs** as its denominator.

| Alphabet | States | SDS=0 (% of all) | Mean SDS | Mean positive SDS | SDS ≥3 (count) | SDS ≥3 (% of positive) | Maximum |
|---|---|---|---|---|---|---|---|
| 2 | 10 vs 20 | 50.010% | 0.6352 | 1.2707 | 2,208 | 1.7667% | 5 |
| 2 | 10 vs 30 | 50.013% | 0.6348 | 1.2699 | 2,212 | 1.7701% | 4 |
| 2 | 20 vs 30 | 49.846% | 0.6367 | 1.2695 | 2,155 | 1.7187% | 4 |
| 3 | 10 vs 20 | 50.221% | 0.5618 | 1.1285 | 76 | 0.0611% | 3 |
| 3 | 10 vs 30 | 49.871% | 0.5648 | 1.1266 | 58 | 0.0463% | 3 |
| 3 | 20 vs 30 | 50.067% | 0.5623 | 1.1261 | 41 | 0.0328% | 3 |
| 4 | 10 vs 20 | 49.997% | 0.5326 | 1.0652 | 2 | 0.0016% | 3 |
| 4 | 10 vs 30 | 50.013% | 0.5338 | 1.0680 | 0 | 0.0000% | 2 |
| 4 | 20 vs 30 | 50.013% | 0.5317 | 1.0636 | 0 | 0.0000% | 2 |
| 5 | 10 vs 20 | 49.957% | 0.5162 | 1.0315 | 0 | 0.0000% | 2 |
| 5 | 10 vs 30 | 50.014% | 0.5156 | 1.0314 | 0 | 0.0000% | 2 |
| 5 | 20 vs 30 | 50.010% | 0.5156 | 1.0314 | 0 | 0.0000% | 2 |

## Exact SDS counts

Each row totals 250,000 pairs; there are no equivalent pairs and no cross-state SDS lengths above 5.

| Alphabet | States | SDS=0 | SDS=1 | SDS=2 | SDS=3 | SDS=4 | SDS=5 |
|---|---|---|---|---|---|---|---|
| 2 | 10 vs 20 | 125,024 | 93,427 | 29,341 | 2,144 | 60 | 4 |
| 2 | 10 vs 30 | 125,032 | 93,468 | 29,288 | 2,192 | 20 | 0 |
| 2 | 20 vs 30 | 124,616 | 93,767 | 29,462 | 2,140 | 15 | 0 |
| 3 | 10 vs 20 | 125,552 | 108,528 | 15,844 | 76 | 0 | 0 |
| 3 | 10 vs 30 | 124,678 | 109,509 | 15,755 | 58 | 0 | 0 |
| 3 | 20 vs 30 | 125,168 | 109,136 | 15,655 | 41 | 0 | 0 |
| 4 | 10 vs 20 | 124,992 | 116,864 | 8,142 | 2 | 0 | 0 |
| 4 | 10 vs 30 | 125,032 | 116,474 | 8,494 | 0 | 0 | 0 |
| 4 | 20 vs 30 | 125,032 | 117,018 | 7,950 | 0 | 0 | 0 |
| 5 | 10 vs 20 | 124,892 | 121,171 | 3,937 | 0 | 0 | 0 |
| 5 | 10 vs 30 | 125,036 | 121,038 | 3,926 | 0 | 0 | 0 |
| 5 | 20 vs 30 | 125,024 | 121,058 | 3,918 | 0 | 0 | 0 |

## Agreement and weighted Jaccard

All entries are mean scores shown as percentages. The positive-SDS columns exclude empty-string distinctions; these pairs agree on the empty string. Agreement includes joint rejection; Jaccard compares accepted-language overlap.

| Alphabet | States | Agreement: all | Jaccard: all | Agreement: positive SDS | Jaccard: positive SDS |
|---|---|---|---|---|---|
| 2 | 10 vs 20 | 50.030% | 30.763% | 58.574% | 37.406% |
| 2 | 10 vs 30 | 50.010% | 30.878% | 58.397% | 37.418% |
| 2 | 20 vs 30 | 50.014% | 31.564% | 58.379% | 37.948% |
| 3 | 10 vs 20 | 49.959% | 31.778% | 58.527% | 38.489% |
| 3 | 10 vs 30 | 50.013% | 31.405% | 58.449% | 37.669% |
| 3 | 20 vs 30 | 49.980% | 32.561% | 58.372% | 39.553% |
| 4 | 10 vs 20 | 50.005% | 32.203% | 58.566% | 39.097% |
| 4 | 10 vs 30 | 49.974% | 32.141% | 58.492% | 38.825% |
| 4 | 20 vs 30 | 50.002% | 32.172% | 58.458% | 38.922% |
| 5 | 10 vs 20 | 49.985% | 32.298% | 58.449% | 38.810% |
| 5 | 10 vs 30 | 49.984% | 32.507% | 58.436% | 39.195% |
| 5 | 20 vs 30 | 50.011% | 32.241% | 58.404% | 39.066% |

## Comparison with same-state-size pairs

The baseline pools the saved **10-, 20-, and 30-state within-batch** results from the same source DFAs and H=5. States 15/25 are excluded from both sides. Within: 374,250 pairs per alphabet; cross: 750,000. Differences are cross minus within, calculated before rounding; pp = percentage points. Similarity means include all pairs, including any equivalent baseline pairs.

| Alphabet | Positive mean: within | Positive mean: cross | Difference | SDS ≥3: within (% of positive) | SDS ≥3: cross (% of positive) |
|---|---|---|---|---|---|
| 2 | 1.2686 | 1.2700 | +0.0014 | 1.7316% | 1.7518% |
| 3 | 1.1266 | 1.1271 | +0.0004 | 0.0645% | 0.0467% |
| 4 | 1.0677 | 1.0656 | -0.0021 | 0.0021% | 0.0005% |
| 5 | 1.0317 | 1.0314 | -0.0003 | 0.0000% | 0.0000% |

| Alphabet | Agreement: within | Agreement: cross | Difference (pp) | Jaccard: within | Jaccard: cross | Difference (pp) |
|---|---|---|---|---|---|---|
| 2 | 50.007% | 50.018% | +0.0113 | 31.103% | 31.068% | -0.0344 |
| 3 | 50.007% | 49.984% | -0.0224 | 31.955% | 31.915% | -0.0407 |
| 4 | 49.983% | 49.993% | +0.0101 | 32.180% | 32.172% | -0.0078 |
| 5 | 49.988% | 49.993% | +0.0057 | 32.357% | 32.349% | -0.0082 |

## Sources and checks

| Input | Identifier |
|---|---|
| Source DFA run | `2026-11-15_19-36-35-433280_UTC` |
| Cross-state result run | `2026-11-15_21-03-45-337283_UTC` |
| Matched within-state result run | `2026-11-15_19-55-50-157162_UTC` |

| Alphabet | Cross-state results (three combinations) |
|---|---|
| 2 | [Saved results](../alphabet_2/cross_state/2026-11-15_19-36-35-433280_UTC/2026-11-15_21-03-45-337283_UTC/) |
| 3 | [Saved results](../alphabet_3/cross_state/2026-11-15_19-36-35-433280_UTC/2026-11-15_21-03-45-337283_UTC/) |
| 4 | [Saved results](../alphabet_4/cross_state/2026-11-15_19-36-35-433280_UTC/2026-11-15_21-03-45-337283_UTC/) |
| 5 | [Saved results](../alphabet_5/cross_state/2026-11-15_19-36-35-433280_UTC/2026-11-15_21-03-45-337283_UTC/) |

Validated all **4,497,000 saved pair rows**: complete Cartesian/unordered pair coverage, unique pair keys, source hashes, manifest counts/SDS histograms, score ranges and metric identities, and matching similarity distributions. No DFA generation or pair calculations were rerun.

These are descriptive results: pairs share DFAs and are not independent samples. A bounded similarity score of 100% does not establish language equivalence.
