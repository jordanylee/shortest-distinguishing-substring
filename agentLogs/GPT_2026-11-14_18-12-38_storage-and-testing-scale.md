# Session Log: Storage and Testing Scale

- Agent: GPT
- Date and time: November 14, 2026, 18:12:38 (America/Chicago)
- Purpose: Answer questions about upstream pickle granularity, batch storage, and feasibility of testing hundreds of DFAs.

## Inspection and Measurements

- Confirmed that `DeepDFA/do_experiments.py` loads one file per state/alphabet/sample index and reads that object's transitions and acceptance flags.
- Found 30 `.pckl` files totaling 23,275 bytes. Inspected pickle opcodes for two representative samples: each has one Random_DFA object construction. Example sizes: 397 bytes for 10 states/2 symbols; 1,246 bytes for 30 states/3 symbols.
- Ran an in-memory benchmark using seed 42, upstream Random_DFA generation, compact integer transition tables, and breadth-first search over state pairs. No datasets or implementation files were saved.
- For 200 DFAs with 30 states and 3 symbols: 19,900 comparisons took 0.109 seconds. Compact JSON Lines records totaled 106,482 bytes, or 21,228 bytes with gzip.
- For 200 DFAs with 100 states and 4 symbols: 19,900 comparisons took 0.122 seconds. Compact JSON Lines records totaled 395,817 bytes, or 109,277 bytes with gzip.
- These timings exclude generation, serialization, and disk I/O. Searches stop at the first acceptance mismatch, sufficient to determine shortest length; witness reconstruction was not benchmarked. Both batches had zero equivalent pairs and examined about two state pairs per comparison on average. These easy random inputs are not worst-case benchmarks or completed research experiments.

## Recommendation

- Revise the proposed storage to a batch `dfas.jsonl.gz` plus a manifest per run and parameter combination, rather than one file per DFA. Include explicit symbol order in the manifest and per-record IDs, seeds, transitions, and acceptance flags.
- Pairwise testing is quadratic in sample count; each product-automaton BFS takes at most O(alphabet_size * states_1 * states_2) time and O(states_1 * states_2) auxiliary memory.
- Preserve empty-string distinctions (roughly half of independent pairs under the generator's acceptance sampling); optionally report conditional distributions separately.
- No generator implementation was created and `time-sensitive.md` remains unchanged pending plan approval.
