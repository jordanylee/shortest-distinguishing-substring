# Additional comparisons: 5, 10 and 15 states

| Setting | Value |
|---|---|
| Source run | `2026-11-15_21-32-55-118406_UTC` |
| Comparison run | `2026-11-15_21-33-59-533782_UTC` |
| Similarity horizon | H=5; uniform length 0–5, then uniform symbols |
| Pairing | All unordered pairs within each alphabet/state batch |
| SDS convention | 0 = empty-string distinction; equivalent = no finite SDS |

| Sampling | Value |
|---|---|
| Master seed | 20 (earlier full sample used 42) |
| Filter | None; all generated DFAs retained |
| Configurations | Alphabets 2/3 × states 5/10/15 |
| DFAs per configuration | 500 |
| Total DFAs | 3,000 |
| Pairs per configuration | 124,750 |
| Total pairs | 748,500 |

## Exact SDS counts — alphabet 2

| States | SDS 0 | SDS 1 | SDS 2 | SDS 3 | SDS 4 | SDS 5 | Equivalent | Total pairs |
|---|---|---|---|---|---|---|---|---|
| 5 | 62,356 | 45,446 | 14,228 | 1,878 | 120 | 4 | 718 | 124,750 |
| 10 | 62,484 | 46,282 | 14,722 | 1,202 | 55 | 0 | 5 | 124,750 |
| 15 | 62,484 | 46,722 | 14,472 | 1,056 | 16 | 0 | 0 | 124,750 |

## Exact SDS counts — alphabet 3

| States | SDS 0 | SDS 1 | SDS 2 | SDS 3 | SDS 4 | SDS 5 | Equivalent | Total pairs |
|---|---|---|---|---|---|---|---|---|
| 5 | 62,491 | 53,913 | 7,846 | 161 | 2 | 0 | 337 | 124,750 |
| 10 | 62,491 | 54,399 | 7,813 | 47 | 0 | 0 | 0 | 124,750 |
| 15 | 61,924 | 54,607 | 8,180 | 39 | 0 | 0 | 0 | 124,750 |

## SDS summary

| Alphabet | States | Mean finite SDS | Mean positive SDS | Maximum SDS | SDS ≥3 pairs | SDS ≥3 % of positive pairs | Equivalent % |
|---|---|---|---|---|---|---|---|
| 2 | 5 | 0.6453 | 1.2977 | 5 | 2,002 | 3.246 | 0.576 |
| 2 | 10 | 0.6377 | 1.2777 | 4 | 1,257 | 2.019 | 0.004 |
| 2 | 15 | 0.6324 | 1.2671 | 4 | 1,072 | 1.722 | 0.000 |
| 3 | 5 | 0.5634 | 1.1320 | 4 | 163 | 0.263 | 0.270 |
| 3 | 10 | 0.5625 | 1.1270 | 3 | 47 | 0.075 | 0.000 |
| 3 | 15 | 0.5698 | 1.1314 | 3 | 39 | 0.062 | 0.000 |

Finite means include SDS=0; positive means exclude it. Both exclude equivalent pairs.

## Mean similarities (H=5)

| Alphabet | States | Agreement | Weighted Jaccard |
|---|---|---|---|
| 2 | 5 | 0.4999 | 0.3054 |
| 2 | 10 | 0.4999 | 0.3165 |
| 2 | 15 | 0.4999 | 0.3128 |
| 3 | 5 | 0.4996 | 0.3045 |
| 3 | 10 | 0.4998 | 0.3231 |
| 3 | 15 | 0.5005 | 0.3137 |

Similarity means include all pairs. The new binary/5-state batch has **four pairs with SDS=5**, confirming that length 5 is not forbidden. Pairs sharing DFAs are dependent.
