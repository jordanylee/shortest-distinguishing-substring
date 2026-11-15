# Current Project Status

Last updated: November 14, 2026, 19:55 (America/Chicago).

The DeepDFA generator has been implemented and validated. Open `/data/DFA_Generator.ipynb`, edit the first cell, and run all cells. `/data/DFA_Generator.py` is the matching notebook-style Python companion. DeepDFA is present as a Git submodule in `/DeepDFA`, and the `/data`, `/code`, and `/agentLogs` directories exist.

The notebook is ready to run with 500 DFAs per combination. Its editable starting defaults are state counts `[10, 20, 30]`, alphabet sizes `[2, 3]`, and master seed `42` (3,000 DFAs total); these are starting settings, not a finalized experimental design. Tests used temporary output directories, which were removed. The exploratory run has not been carried out, and no empirical hypothesis has been formed.

Two runs with these defaults are committed under `data/alphabet_<A>/states_<S>/`: `2026-11-15_00-30-21-627385_UTC` (gzip) and `2026-11-15_00-36-37-375402_UTC` (plain `.jsonl`). Their records are identical (same master seed), so they are not independent samples. **Use the newer `2026-11-15_00-36-37-375402_UTC` run as the canonical exploratory input.**

The shortest-distinguishing-string code from [code/IMPLEMENTATION_PLAN.md](code/IMPLEMENTATION_PLAN.md) is **implemented and tested** (`code/loader.py`, `distinguish.py`, `dfa_stats.py`, `pairs.py`, driver `run_pairs.py`; tests via `python3.12 -m unittest discover -s code/tests -t code`, 32 tests, about 3 s). Use `python3.12`; the default `python3` on this machine is 3.10. A separate plan for similarity metrics is in [similarity-metrics.md](similarity-metrics.md) (not yet implemented).

## Exploratory Results (canonical run)

Results id `2026-11-15_01-51-53-783405_UTC`, stored at `data/alphabet_<A>/states_<S>/2026-11-15_00-36-37-375402_UTC/pairs/2026-11-15_01-51-53-783405_UTC/` (`pairs.jsonl.gz` with length and shortlex-smallest witness per pair, `dfa_stats.jsonl.gz` with reachable and minimal sizes, `manifest.json` with histograms and provenance). Produced from clean commit `d763ecf`; the full run took about 13 s. No visualizations yet.

| Alphabet | States | Equivalent pairs | Length histogram (0, 1, 2, 3, 4, 5, 6) | Max length |
|---|---|---|---|---|
| 2 | 10 | 37 | 62499, 46613, 14400, 1124, 68, 0, 9 | 6 |
| 2 | 20 | 0 | 62356, 46680, 14659, 1044, 10, 1, 0 | 5 |
| 2 | 30 | 0 | 62244, 46914, 14608, 975, 9, 0, 0 | 4 |
| 3 | 10 | 0 | 61971, 54625, 8077, 77, 0, 0, 0 | 3 |
| 3 | 20 | 0 | 62356, 54649, 7724, 21, 0, 0, 0 | 3 |
| 3 | 30 | 0 | 62451, 54576, 7700, 23, 0, 0, 0 | 3 |

Each batch has 124,750 pairs (dependent observations; see below). Equivalent counts and max lengths match GPT's earlier benchmark. Preliminary observations, not yet a hypothesis: about half of pairs differ on the empty string; lengths are very short and the maximum *decreases* as state count grows; a larger alphabet shortens lengths further. The 37 equivalent pairs in alphabet 2/states 10 involve DFAs with trivial languages (11 DFAs there have minimal size 1). Minimal sizes are typically somewhat below the raw state count, mostly because of unreachable states (see the `minimal_histogram` and `reachable_histogram` fields in each results manifest).

## Generator Validation

- Generated and reloaded all 3,000 default samples in a temporary directory, checking each against regeneration from its recorded seed. Generation and verification took approximately 3.08 seconds locally.
- Executed the native notebook through a Jupyter kernel from a `data` working directory, using small batches that included one-state DFAs, unary alphabets, and an 11-symbol alphabet.
- Confirmed existing runs cannot be overwritten, invalid parameter values are rejected, the caller's global random state is preserved, and changing parameter-list order preserves the generated DFA records.
- Saved notebooks contain no test execution outputs or temporary paths. These checks validate generation and storage; they do not implement shortest-distinguishing-string experiments.

## Generator Findings

- `DeepDFA/Random_DFA.py` defines the class `Random_DFA(number_of_states, number_of_symbols)`. Generation requires only Python's standard-library `random` module, not PyTorch or Pythomata.
- Instances contain a transition dictionary and an acceptance-flag list. State 0 is the implicit initial state. The constructor does not save files; upstream `.pckl` samples each contain one DFA.
- Sampling forces a forward transition from each state except the last and randomly fills the remaining transitions. This is not uniform sampling over complete DFAs and does not guarantee reachability or minimality.
- Transition symbols are strings such as `"0"` and `"10"`. The concatenated alphabet attribute and character-based acceptance helper are unsuitable for alphabets larger than 10 symbols. Export explicit symbol lists and use symbol sequences when evaluating these DFAs.
- Inspected DeepDFA revision: `e74c5f5b7371952060d7b2abfae29b42fba784ce`. Python 3.12.2, Jupyter notebook, and ipykernel are available in the inspected environment.

## Approved Generator Plan

1. Provide `/data/DFA_Generator.ipynb` as a native Jupyter notebook and `/data/DFA_Generator.py` as its matching `# %%` Python companion. Both are implemented; keep their cell content synchronized when editing.
2. Expose a starting configuration cell for alphabet sizes, state counts, a master random seed, and **500 DFAs per alphabet-size/state-count combination**. Defaults are listed above; review them before a production run.
3. Import the existing DeepDFA generator without modifying the submodule. Assign and record a reproducible seed for each sample.
4. Store one compressed JSON Lines batch and a manifest per combination and run:

   ```text
   data/
     DFA_Generator.ipynb
     DFA_Generator.py
     alphabet_<A>/
       states_<S>/
         <run_id>/
           manifest.json
           dfas.jsonl.gz
   ```

5. Each JSON line represents one DFA, with an ID, seed, initial state, compact transition table, and acceptance flags. The manifest specifies the explicit alphabet and its column order, state count, sample count, generation parameters, seed scheme, Python version, and DeepDFA commit. Avoid overwriting existing runs.
6. Validate transition completeness, destination ranges, acceptance-list length, seed reproducibility, and serialization round trips before bulk generation. Preserve raw samples without minimization or rejection; equivalence checks belong to the later experiments.

## Approved Exploratory Testing Plan

1. Compare every unique unordered pair within each generated batch having the same state count and alphabet size. For 500 DFAs, compare DFA 1 with DFAs 2-500, DFA 2 with DFAs 3-500, and so on: **124,750 comparisons per parameter combination**. Exclude self-comparisons and reversed duplicates. Initially keep different state counts separate; comparisons across state counts with the same alphabet are a possible later experiment.
2. For each pair, use breadth-first search over pairs of states, starting from the two initial states and following the same symbol through both DFAs. The first reachable pair with different acceptance flags gives the shortest distinguishing length, equal to the search depth. If all reachable state pairs agree on acceptance, the two languages are equivalent. This avoids enumerating strings.
3. Save comparison results in `/data`, identifying the source run, parameter combination, and both DFA IDs. Record equivalent pairs separately from finite distinguishing lengths; equivalent pairs have no distinguishing string and must not be assigned length zero.
4. Report the shortest-length distribution for non-equivalent pairs, retaining empty-string distinctions at length zero. Also report the equivalent-pair count and rate. A distribution conditional on positive distinguishing length can supplement the full distribution.
5. Treat comparisons sharing a DFA as dependent observations. The 124,750 comparisons are not 124,750 independent samples. For later hypothesis testing, account for this dependence, for example by repeating the experiment with independently generated batches.

This testing plan is implemented in `/code` and has been run on the canonical batches.

## Testing Considerations

- There are 124,750 unordered pairs within a batch of 500 DFAs. Use breadth-first search over state pairs to find shortest distinguishing lengths or establish equivalence, rather than enumerating strings.
- A comparison takes at most O(alphabet_size * states_1 * states_2) time and O(states_1 * states_2) auxiliary memory. Preliminary in-memory checks on 200 random DFAs at 30 states/3 symbols and 100 states/4 symbols were fast, but do not establish worst-case performance.
- Retain empty-string distinctions (length zero), expected for about half of independent pairs under the generator's acceptance sampling. A separate conditional distribution for positive lengths can supplement the full distribution.

## Next Steps

1. Review the notebook's starting state counts, alphabet sizes, and master seed for the exploratory run; sample count is fixed at 500 per combination.
2. Generate production batches if the defaults change; otherwise use the canonical run above. The exploratory pairing strategy is the approved within-batch all-pairs plan above.
3. Done: distinguishing-string code implemented and run on the canonical batches (see "Exploratory Results").
4. Analyze and visualize the saved results (save plots in `/data`), including the conditional positive-length distribution and how length relates to the per-DFA minimal sizes. Account for within-batch dependence (for example, independently seeded batches or disjoint-pair subsampling).
   - Deferred by user decision: choosing the similarity-metric horizon `H` (see `similarity-metrics.md`). That plan asks for `H` to be fixed before distinguishing lengths are examined. If `H` is chosen after these results are seen, record that the similarity metrics are descriptive, not a pre-registered test.
5. Form a hypothesis from the observed distributions and design tailored follow-up simulations.
