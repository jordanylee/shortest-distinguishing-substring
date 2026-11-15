# Session Log: Existing Batch Runtime Benchmark

- Agent: GPT
- Session started: November 14, 2026, 18:44:44 (America/Chicago)
- Purpose: Estimate exploratory comparison runtime using the actual saved DFA batches.

## Inspection and Benchmark

- Found two runs, each with six parameter combinations and 500 DFAs per combination. One stores gzip JSON Lines; the other stores uncompressed JSON Lines. Read filenames and metadata from each manifest rather than assuming fixed filenames.
- Compared parsed records across runs for each parameter combination. All six corresponding batches are identical, including sample IDs, seeds, transitions, and acceptance flags; the runs are not independent samples.
- Ran an ephemeral Python breadth-first search over state pairs for every unique unordered pair within every saved batch. Returned shortest distinguishing lengths or None for equivalent languages and accumulated in-memory histograms. No result datasets or reusable experiment implementation were written.
- Each batch contains 124,750 comparisons. Times for the six combinations in the first run were approximately 0.489, 0.514, 0.515, 0.581, 0.576, and 0.577 seconds; corresponding second-run times were 0.497, 0.502, 0.505, 0.595, 0.598, and 0.591 seconds.
- Total: 1,497,000 comparisons across all 12 batches, 6.748 seconds including batch reads. Testing one copy of each combination requires 748,500 comparisons and roughly 3.3 seconds of comparison time on this machine.
- Observed 37 equivalent pairs in each copy of the alphabet-2/state-10 batch and none in the other batches. Longest observed finite lengths ranged from 3 to 6 depending on combination. These are preliminary benchmark observations, not a validated saved research result set.

## Limits

- Timing includes length/equivalence computation and histogram accumulation, but excludes per-pair result serialization, witness reconstruction, plotting, and rigorous validation of a production testing implementation.
- No source, notebooks, or existing datasets were modified. Only this session log was added.
