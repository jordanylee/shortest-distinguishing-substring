# Current Project Status

Last updated: November 14, 2026 (America/Chicago).

The DeepDFA generation workflow has been inspected, and the user has approved the generator plan below. DeepDFA is present as a Git submodule in `/DeepDFA`, and the `/data`, `/code`, and `/agentLogs` directories exist. The root README records the research question, experimental approach, and repository guidelines.

No project experiment code, generated datasets, results, or visualizations are present in `/code` or `/data` yet. The exploratory run has not been carried out, and no empirical hypothesis has been formed.

## Generator Findings

- `DeepDFA/Random_DFA.py` defines the class `Random_DFA(number_of_states, number_of_symbols)`. Generation requires only Python's standard-library `random` module, not PyTorch or Pythomata.
- Instances contain a transition dictionary and an acceptance-flag list. State 0 is the implicit initial state. The constructor does not save files; upstream `.pckl` samples each contain one DFA.
- Sampling forces a forward transition from each state except the last and randomly fills the remaining transitions. This is not uniform sampling over complete DFAs and does not guarantee reachability or minimality.
- Transition symbols are strings such as `"0"` and `"10"`. The concatenated alphabet attribute and character-based acceptance helper are unsuitable for alphabets larger than 10 symbols. Export explicit symbol lists and use symbol sequences when evaluating these DFAs.
- Inspected DeepDFA revision: `e74c5f5b7371952060d7b2abfae29b42fba784ce`. Python 3.12.2, Jupyter notebook, and ipykernel are available in the inspected environment.

## Approved Generator Plan

1. Create `/data/DFA_Generator.py` with notebook-style `# %%` cells, as discussed. This is a Python file supporting cell execution in compatible editors; a native Jupyter notebook would use `.ipynb`.
2. Expose configuration cells for alphabet sizes, state counts, a master random seed, and **500 DFAs per alphabet-size/state-count combination**. The alphabet sizes, state counts, and master seed still need to be selected.
3. Import the existing DeepDFA generator without modifying the submodule. Assign and record a reproducible seed for each sample.
4. Store one compressed JSON Lines batch and a manifest per combination and run:

   ```text
   data/
     DFA_Generator.py
     alphabet_<A>/
       states_<S>/
         <run_id>/
           manifest.json
           dfas.jsonl.gz
   ```

5. Each JSON line represents one DFA, with an ID, seed, initial state, compact transition table, and acceptance flags. The manifest specifies the explicit alphabet and its column order, state count, sample count, generation parameters, seed scheme, Python version, and DeepDFA commit. Avoid overwriting existing runs.
6. Validate transition completeness, destination ranges, acceptance-list length, seed reproducibility, and serialization round trips before bulk generation. Preserve raw samples without minimization or rejection; equivalence checks belong to the later experiments.

## Testing Considerations

- There are 124,750 unordered pairs within a batch of 500 DFAs. Use breadth-first search over state pairs to find shortest distinguishing lengths or establish equivalence, rather than enumerating strings.
- A comparison takes at most O(alphabet_size * states_1 * states_2) time and O(states_1 * states_2) auxiliary memory. Preliminary in-memory checks on 200 random DFAs at 30 states/3 symbols and 100 states/4 symbols were fast, but do not establish worst-case performance.
- Retain empty-string distinctions (length zero), expected for about half of independent pairs under the generator's acceptance sampling. A separate conditional distribution for positive lengths can supplement the full distribution.

## Next Steps

1. Implement and validate the approved generator notebook-style Python file.
2. Select exploratory state counts, alphabet sizes, pairing strategy, and random seeds; sample count is fixed at 500 per combination.
3. Implement and validate code in `/code` to detect equivalent pairs and find shortest distinguishing strings for non-equivalent pairs.
4. Run the exploratory simulations and save results and visualizations in `/data`.
5. Form a hypothesis from the observed distributions and design tailored follow-up simulations.
