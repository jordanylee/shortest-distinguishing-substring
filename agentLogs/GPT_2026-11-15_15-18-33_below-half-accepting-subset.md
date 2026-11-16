# Compare strictly below-half accepting DFAs

Agent GPT; November 15, 2026, America/Chicago.

User requested a script calculating SDS and both similarity metrics on existing DFAs with <50% accepting states for alphabets 2 and 3. Added `code/run_below_half.py` with read-only preview by default and `--run --horizon H` execution. Default source is `2026-11-15_19-36-35-433280_UTC`, states 10/15/20/25/30. All selected batches are checked for availability; destinations are checked before computation. Each batch compares all unordered pairs whose two endpoints pass the strict filter; no cross-state comparisons or generation.

Extended `code/experiments.py` with a strict integer predicate and optional `below_half_only` selection. Default unfiltered behavior and paths remain unchanged. Subset calculations reuse the established SDS/similarity/statistics functions and existing writer/atomic output lifecycle. They write to `comparisons_below_half/<results_id>/`. Manifests include source size, selected IDs, accepting-state counts and initial acceptance flags, selection definition and source/script provenance. Raw states, including unreachable states, define the denominator. Exactly 50% is excluded; empty languages are included.

Preview of production source: alphabet 2 selected sizes 210/260/217/262/216; alphabet 3 selected sizes 197/254/208/246/218. These yield 263,215 pairs total. Production calculations were not run, because the request was to make the script; the README provides the explicit H=5 command matching current comparisons.

Added three meaningful tests in `code/tests/test_below_half.py` for even/odd strict boundaries and unreachable-state treatment, equality to selected full-run pair records with preserved nonconsecutive IDs, isolated storage/no overwrite/missing-batch handling, and valid zero-pair outputs. All three passed. Ran five existing `test_experiments.py` tests; all passed. Test computations used temporary synthetic data. Updated README usage and current project status. Preserved existing raw/results data and unrelated changes.

Interpretation: accepting-state fraction depends on representation, so the subset is not automatically representative of real-world DFAs. Filtering may affect initial acceptance and hence SDS=0 frequency; manifests expose initial flags for later descriptive analysis.
