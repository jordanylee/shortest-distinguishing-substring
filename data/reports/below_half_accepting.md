# DFAs with fewer than 50% accepting states

**Filter:** both DFAs have strictly <50% accepting raw states, including unreachable states. Exactly 50% is excluded. No DFAs were regenerated.

| Setting | Value |
|---|---|
| Source run | `2026-11-15_19-36-35-433280_UTC` |
| Comparison run | `2026-11-15_21-22-02-784266_UTC` |
| Similarity horizon | H=5; uniform length 0–5, then uniform symbols |
| Pairing | All unordered pairs within each alphabet/state batch |
| SDS convention | 0 = empty-string distinction; equivalent = no finite SDS |

## Selected DFAs and pair counts

| Alphabet | States | Source DFAs | Selected DFAs | Retained | Subset pairs |
|---|---|---|---|---|---|
| 2 | 10 | 500 | 210 | 42.0% | 21,945 |
| 2 | 15 | 500 | 260 | 52.0% | 33,670 |
| 2 | 20 | 500 | 217 | 43.4% | 23,436 |
| 2 | 25 | 500 | 262 | 52.4% | 34,191 |
| 2 | 30 | 500 | 216 | 43.2% | 23,220 |
| 3 | 10 | 500 | 197 | 39.4% | 19,306 |
| 3 | 15 | 500 | 254 | 50.8% | 32,131 |
| 3 | 20 | 500 | 208 | 41.6% | 21,528 |
| 3 | 25 | 500 | 246 | 49.2% | 30,135 |
| 3 | 30 | 500 | 218 | 43.6% | 23,653 |
| Total | — | 5000 | 2288 | — | 263,215 |

## Exact SDS counts — alphabet 2

| States | SDS 0 | SDS 1 | SDS 2 | SDS 3 | SDS 4 | SDS 5 | SDS 6 | Equivalent | Total pairs |
|---|---|---|---|---|---|---|---|---|---|
| 10 | 10,064 | 8,451 | 3,013 | 333 | 48 | 0 | 8 | 28 | 21,945 |
| 15 | 16,059 | 12,956 | 4,286 | 364 | 4 | 0 | 1 | 0 | 33,670 |
| 20 | 10,780 | 9,160 | 3,251 | 245 | 0 | 0 | 0 | 0 | 23,436 |
| 25 | 16,377 | 13,134 | 4,371 | 308 | 1 | 0 | 0 | 0 | 34,191 |
| 30 | 11,135 | 8,918 | 2,930 | 233 | 4 | 0 | 0 | 0 | 23,220 |

## Exact SDS counts — alphabet 3

| States | SDS 0 | SDS 1 | SDS 2 | SDS 3 | SDS 4 | SDS 5 | SDS 6 | Equivalent | Total pairs |
|---|---|---|---|---|---|---|---|---|---|
| 10 | 8,296 | 8,871 | 2,095 | 44 | 0 | 0 | 0 | 0 | 19,306 |
| 15 | 15,805 | 13,983 | 2,322 | 21 | 0 | 0 | 0 | 0 | 32,131 |
| 20 | 10,287 | 9,701 | 1,532 | 8 | 0 | 0 | 0 | 0 | 21,528 |
| 25 | 14,873 | 12,949 | 2,309 | 4 | 0 | 0 | 0 | 0 | 30,135 |
| 30 | 11,520 | 10,584 | 1,545 | 4 | 0 | 0 | 0 | 0 | 23,653 |

## SDS: full sample versus filtered subset

“Positive” excludes SDS=0 and equivalent pairs. Tail percentages use positive finite pairs as the denominator.

| Alphabet | States | SDS=0 % full | SDS=0 % subset | Positive mean full | Positive mean subset | SDS ≥3 % full | SDS ≥3 % subset |
|---|---|---|---|---|---|---|---|
| 2 | 10 | 50.10 | 45.86 | 1.2716 | 1.3259 | 1.930 | 3.282 |
| 2 | 15 | 50.10 | 47.70 | 1.2660 | 1.2857 | 1.693 | 2.095 |
| 2 | 20 | 49.98 | 46.00 | 1.2690 | 1.2956 | 1.691 | 1.936 |
| 2 | 25 | 50.07 | 47.90 | 1.2667 | 1.2801 | 1.641 | 1.735 |
| 2 | 30 | 49.89 | 47.95 | 1.2653 | 1.2820 | 1.574 | 1.961 |
| 3 | 10 | 49.68 | 42.97 | 1.1311 | 1.1983 | 0.123 | 0.400 |
| 3 | 15 | 49.81 | 49.19 | 1.1288 | 1.1448 | 0.075 | 0.129 |
| 3 | 20 | 49.98 | 47.78 | 1.1245 | 1.1377 | 0.034 | 0.071 |
| 3 | 25 | 49.94 | 49.35 | 1.1288 | 1.1518 | 0.029 | 0.026 |
| 3 | 30 | 50.06 | 48.70 | 1.1243 | 1.1280 | 0.037 | 0.033 |

## Mean similarities: full sample versus filtered subset

Means include all pairs, including length zero and equivalent pairs.

| Alphabet | States | Agreement full | Agreement subset | Jaccard full | Jaccard subset |
|---|---|---|---|---|---|
| 2 | 10 | 0.5002 | 0.5548 | 0.3020 | 0.1877 |
| 2 | 15 | 0.4995 | 0.5194 | 0.3239 | 0.2430 |
| 2 | 20 | 0.5000 | 0.5255 | 0.3140 | 0.2348 |
| 2 | 25 | 0.4997 | 0.5135 | 0.3234 | 0.2583 |
| 2 | 30 | 0.5000 | 0.5157 | 0.3171 | 0.2524 |
| 3 | 10 | 0.5005 | 0.5684 | 0.3073 | 0.1762 |
| 3 | 15 | 0.5003 | 0.5182 | 0.3266 | 0.2442 |
| 3 | 20 | 0.4998 | 0.5219 | 0.3296 | 0.2384 |
| 3 | 25 | 0.5000 | 0.5168 | 0.3244 | 0.2533 |
| 3 | 30 | 0.4998 | 0.5137 | 0.3218 | 0.2568 |

Full-sample comparison ID: `2026-11-15_19-55-50-157162_UTC`. These are descriptive, overlapping samples; pairs share DFAs.

## The missing length-5 count

| Sample | Alphabet | States | Pairs with SDS=5 |
|---|---|---|---|
| Filtered subset | 2 | 10 | 0 |
| Filtered subset | 2 | 15 | 0 |
| Earlier full sample | 2 | 15 | 4 |
| Earlier full sample | 2 | 20 | 1 |
| Additional seed-20 sample | 2 | 5 | 4 |

Length 5 is possible. Its absence in the filtered subset is a sample observation; no explanation for that particular gap has been established.
