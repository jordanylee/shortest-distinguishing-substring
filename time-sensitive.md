# Current Project Status

Last updated: November 14, 2026 (America/Chicago).

The DeepDFA generator has been implemented and validated. Open `/data/DFA_Generator.ipynb`, edit the first cell, and run all cells. `/data/DFA_Generator.py` is the matching notebook-style Python companion. DeepDFA is present as a Git submodule in `/DeepDFA`, and the `/data`, `/code`, and `/agentLogs` directories exist.

The notebook is ready to run with 500 DFAs per combination. Its editable starting defaults are state counts `[10, 20, 30]`, alphabet sizes `[2, 3]`, and master seed `42` (3,000 DFAs total); these are starting settings, not a finalized experimental design. Tests used temporary output directories, which were removed. The exploratory run has not been carried out, and no empirical hypothesis has been formed.

Two runs with these defaults are committed under `data/alphabet_<A>/states_<S>/`: `2026-11-15_00-30-21-627385_UTC` (gzip) and `2026-11-15_00-36-37-375402_UTC` (plain `.jsonl`). Their records are identical (same master seed), so they are not independent samples. **Use the newer `2026-11-15_00-36-37-375402_UTC` run as the canonical exploratory input.** No comparison results or visualizations exist yet.

An implementation plan for the shortest-distinguishing-string code is recorded in [code/IMPLEMENTATION_PLAN.md](code/IMPLEMENTATION_PLAN.md) (not yet implemented). A separate plan for similarity metrics is in [similarity-metrics.md](similarity-metrics.md).

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

Implementation of this approved testing plan is still pending; the generator's storage and replay checks do not perform these experiments.

## Testing Considerations

- There are 124,750 unordered pairs within a batch of 500 DFAs. Use breadth-first search over state pairs to find shortest distinguishing lengths or establish equivalence, rather than enumerating strings.
- A comparison takes at most O(alphabet_size * states_1 * states_2) time and O(states_1 * states_2) auxiliary memory. Preliminary in-memory checks on 200 random DFAs at 30 states/3 symbols and 100 states/4 symbols were fast, but do not establish worst-case performance.
- Retain empty-string distinctions (length zero), expected for about half of independent pairs under the generator's acceptance sampling. A separate conditional distribution for positive lengths can supplement the full distribution.

## Next Steps

1. Review the notebook's starting state counts, alphabet sizes, and master seed for the exploratory run; sample count is fixed at 500 per combination.
2. Generate production batches if the defaults change; otherwise use the canonical run above. The exploratory pairing strategy is the approved within-batch all-pairs plan above.
3. Implement and validate code in `/code` to detect equivalent pairs and find shortest distinguishing strings for non-equivalent pairs, following [code/IMPLEMENTATION_PLAN.md](code/IMPLEMENTATION_PLAN.md).
4. Run the exploratory simulations and save results and visualizations in `/data`.
5. Form a hypothesis from the observed distributions and design tailored follow-up simulations.
