# Two tabular comparison reports

Agent GPT; November 15, 2026, America/Chicago.

Created the two requested Markdown files under `data/reports/`: `below_half_accepting.md` and `additional_comparisons_seed20.md`. Both emphasize tables and concise denominator/interpretation notes. Added `code/write_comparison_tables.py` to reproduce them from explicit saved source/results IDs. Added discoverability links in README and current status.

The subset report includes selected DFAs/pairs, exact per-alphabet SDS counts, positive-SDS and tail comparisons against the matching full sample, and H=5 agreement/Jaccard means. Source `2026-11-15_19-36-35-433280_UTC`, subset `2026-11-15_21-22-02-784266_UTC`, full results `2026-11-15_19-55-50-157162_UTC`.

The new report covers source `2026-11-15_21-32-55-118406_UTC`, results `2026-11-15_21-33-59-533782_UTC`, alphabets 2/3, states 5/10/15, master seed 20 and H=5. Six batches have 500 DFAs and 124,750 pairs each. Reports show exact counts, finite/positive means, positive-tail rates, equivalence rates, and similarity means. The binary/5-state batch has four SDS=5 pairs, disproving any universal missing-length rule. The earlier full seed-42 sample also had SDS=5 pairs. No cause for its absence specifically in the filtered subset was established.

Checked all six new source manifests for seed 20 and count 500, confirmed overlapping 10/15-state source files differ from seed-42 files, and scanned saved pair files for all 26 report input batches. Validated complete manifests, scoped configuration IDs, source hashes, all-pair denominators, histograms/equivalence counts, strict subset predicates and common H=5. Checked all generated Markdown table widths (seven tables in subset report; six in new report), and inspected final contents. No experiments or tests rerun; raw data and unrelated workspace changes preserved.
