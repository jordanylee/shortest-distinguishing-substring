# Current Project Status

Last updated: November 15, 2026 (America/Chicago).

Presentation wrap-up: [PRESENTATION_SUMMARY.md](PRESENTATION_SUMMARY.md) now collects ten 16:9 SVG figures with exact SDS bucket tables, Pearson/Spearman correlations, and quantified within/cross-category overlays. The approved scope covers the original twenty batches, twelve completed cross-state batches, and six High SDS seed-20 batches. `dataviz/presentation_summary.py` validates all 6,243,500 saved pair rows and writes the root summary plus figures/CSVs/provenance in `dataviz/figures/presentation_summary/`. Similarity plots exclude original states 15/25; bucket figures retain them. Independent numerical audit reconciled all 304 bucket rows, 48 correlation rows, 960 bin rows, and eight overlay rows; an adversarial agent inspected all ten figures and the overview, and its layout/rounding findings were fixed. Original/cross curves are close over most pair mass (weighted bin differences below 0.011 symbols, supported coverage at least 99.85%), with larger deviations in individual tail bins. Corrected the presumed alphabet-4 maximum: four within-category and two cross-category pairs have SDS=3; alphabet 5 has none above 2. No experiments rerun; historical outputs preserved.

Comparison table reports: [below-half accepting subset](data/reports/below_half_accepting.md) summarizes completed result `2026-11-15_21-22-02-784266_UTC` and its full-data baseline. [Additional seed-20 comparisons](data/reports/additional_comparisons_seed20.md) summarizes source `2026-11-15_21-32-55-118406_UTC`, results `2026-11-15_21-33-59-533782_UTC`, six batches (alphabets 2/3, states 5/10/15), 748,500 pairs at H=5. The new binary/5-state batch contains four SDS=5 pairs: the absence of length 5 in the filtered subset is not a general restriction. Reports are rebuilt by `code/write_comparison_tables.py` from saved outputs only.

Below-half accepting subset: added `code/run_below_half.py` to preview or calculate SDS and both similarities for alphabets 2/3, within each raw state batch, retaining only DFAs with strictly <50% accepting raw states. Current source defaults yield 263,215 subset pairs across ten batches. Production calculations have not been run; execute `python code/run_below_half.py --run --horizon 5` to match existing full-data H=5. Results use separate `comparisons_below_half/<results_id>/` directories, preserving IDs and recording the filter/selection in manifests. Three new boundary/parity/storage tests and five existing experiment tests passed.

SDS tail-count figure: added `dataviz/sds_tail_counts.py`, parameter notebook, and one SVG under `dataviz/figures/sds_tail_counts/`. Two panels (alphabets 2/3) show counts with finite SDS >= d at thresholds 2–6, five state sizes each, logarithmic count axes. The SVG includes reading instructions, exact tables with zeros, and a worked example (binary/10-state at d=4: 77 pairs). Equivalent pairs excluded; source is saved histogram manifests from the current twenty-configuration comparison run. Companion CSV and provenance included; no experiments rerun.

Notebook fix: optional preview/run cells now refresh their helper modules in dependency order, fixing the reported `sort_ids` TypeError when a persistent kernel has cached the older `experiments._pair_record`. Preserved the user's enabled optional configuration. Verified with a regression reproducing the exact cached-import failure, fresh-kernel notebook checks, and the real 1,200-pair benchmark (15 tests passed). No full cross-state experiment was started.

Similarity layout update: the active SDS/similarity deliverable is now four combined SVGs under `dataviz/figures/sds_vs_similarity/`: agreement/Jaccard by alphabet (2x2 panels) and by states (three panels at 10/20/30). The original fourteen individual figures and their supporting exports are preserved in its `individual/` subfolder. Script, notebook and README now use the combined figures; underlying bins/data are unchanged.

Cross-state comparison support: [code/DFA_Comparisons.ipynb](code/DFA_Comparisons.ipynb) now ends with an **OPTIONAL** section (disabled by default) to compute SDS, agreement, and weighted Jaccard for 10–20, 10–30, and 20–30 states within each alphabet. States 15/25 are excluded. Separate defaults select the current four-alphabet source `2026-11-15_19-36-35-433280_UTC` and saved within-batch H=5. Preview confirms 12 combinations and 3,000,000 pairs. `code/cross_state.py` provides read-only preview/benchmark and streaming output under `data/alphabet_<A>/cross_state/<source_run>/<results_id>/states_<S1>_vs_<S2>/`, with source hashes and state-qualified DFA identities. This session added and tested the workflow; the full cross-state experiment has not been run.

Curated visualization update: active exports are now SVG only. Both state figures were regenerated and their active PNG copies removed. Added [SDS_Similarity.ipynb](dataviz/SDS_Similarity.ipynb) and `dataviz/sds_similarity.py`: seven agreement and seven weighted-Jaccard figures (four alphabet groups, three state groups at 10/20/30), using the same twenty-configuration run below at saved H=5. Similarity bins show mean finite SDS; equivalent pairs excluded, length zero retained. All 2,495,000 pair rows were validated; bin counts and separate provenance are saved alongside the SVGs. See [dataviz/README.md](dataviz/README.md) for figure links. No experiments were rerun; archive preserved.

Visualization restart: the user requested that the earlier visualization workspace be archived. Its code, notebook, figures, tables, and notes are preserved in [archive/dataviz_2026-11-15_14-30-09](archive/dataviz_2026-11-15_14-30-09/); all 57 files were verified by SHA256. The new [dataviz/README.md](dataviz/README.md) links just two figures: reachable-state distributions and minimal-state distributions, each with twenty colored lines and percentages out of 500 DFAs. These use source `2026-11-15_19-36-35-433280_UTC` and saved comparison statistics `2026-11-15_19-55-50-157162_UTC`: alphabets 2–5, generated states 10/15/20/25/30, 10,000 DFAs total. Open [dataviz/State_Distributions.ipynb](dataviz/State_Distributions.ipynb); logic is in its separate script. No experiments were rerun. Older six-batch H=3/H=4 results also remain under data; older statements below that no similarity runs exist are superseded.

The DeepDFA generator has been implemented and validated. Open `/data/DFA_Generator.ipynb`, edit the first cell, and run all cells. `/data/DFA_Generator.py` is the matching notebook-style Python companion. DeepDFA is present as a Git submodule in `/DeepDFA`, and the `/data`, `/code`, and `/agentLogs` directories exist.

The generator notebook is ready to run with 500 DFAs per combination. Its editable starting defaults are state counts `[10, 20, 30]`, alphabet sizes `[2, 3]`, and master seed `42` (3,000 DFAs total); these are starting settings, not a finalized experimental design. The canonical exploratory SDS run has been completed (results below); no empirical hypothesis has been formed.

Two runs with these defaults are committed under `data/alphabet_<A>/states_<S>/`: `2026-11-15_00-30-21-627385_UTC` (gzip) and `2026-11-15_00-36-37-375402_UTC` (plain `.jsonl`). Their records are identical (same master seed), so they are not independent samples. **Use the newer `2026-11-15_00-36-37-375402_UTC` run as the canonical exploratory input.**

The shortest-distinguishing-string code from [code/IMPLEMENTATION_PLAN.md](code/IMPLEMENTATION_PLAN.md) is **implemented and tested**. The original SDS driver `code/run_pairs.py` remains available. Use a Python 3.12 environment; the current Windows `python` is 3.12.2.

The combined experiment interface is now [code/DFA_Comparisons.ipynb](code/DFA_Comparisons.ipynb), with a matching `# %%` Python companion. It supports SDS, similarity, or both, within each selected batch. Calculations live in separate modules: existing loader/BFS/stats, new `similarity_metrics.py`, orchestration in `experiments.py`, and read-only summaries in `result_summary.py`. Edit the configuration cell, set an explicit `HORIZON` for similarity, inspect the preview/benchmark, then execute. New outputs are stored under `comparisons/<results_id>/` in each source batch; old `pairs/` results are preserved.

The [similarity specification](similarity-metrics.md) is implemented using exact integer counts and rational weights/scores, converted to floats only for output. No horizon has been chosen for research and no full similarity run has been generated. Read-only benchmarks sampled 30 pairs from each canonical batch: total pair-calculation estimates were about 2 minutes at H=5 and 50 minutes at H=20 on this machine; these are rough estimates excluding stats, gzip and disk I/O, not experiment results. Rerun the notebook benchmark for the actual chosen horizon.

Validation: `python -B -m unittest discover -s code/tests -t code` passes all 45 tests on Python 3.12.2 (about 20 seconds locally), including actual notebook execution in fresh kernels from both the repository root and `code/`. Notebook outputs are cleared in the saved artifact. Integration tests write only temporary batches/results.

A code review of this implementation was triaged and resolved; see [code/REVIEW_FIXES.md](code/REVIEW_FIXES.md) (six fixes applied in `bebf5d6`, four declined). The fixes do not change results: rerunning the canonical batches with the fixed code reproduced the committed pair and stats files byte for byte, in about 7 s instead of about 10 s.

## Exploratory Results (canonical run)

Results id `2026-11-15_01-51-53-783405_UTC`, stored at `data/alphabet_<A>/states_<S>/2026-11-15_00-36-37-375402_UTC/pairs/2026-11-15_01-51-53-783405_UTC/` (`pairs.jsonl.gz` with length and shortlex-smallest witness per pair, `dfa_stats.jsonl.gz` with reachable and minimal sizes, `manifest.json` with histograms and provenance). Produced from clean commit `d763ecf`; the full run took about 13 s. No visualizations yet. Analysis code should load results by this explicit results id, not by globbing `pairs/*`, so a stray or partial result set cannot be double-counted.

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
   - Done: combined comparison notebook and similarity calculation modules. Next, choose an explicit horizon, benchmark, and run similarity comparisons through the notebook.
4. Analyze and visualize the saved results (save plots in `/data`), including the conditional positive-length distribution and how length relates to the per-DFA minimal sizes. Account for within-batch dependence (for example, independently seeded batches or disjoint-pair subsampling).
   - Deferred by user decision: choosing the similarity-metric horizon `H` (see `similarity-metrics.md`). That plan asks for `H` to be fixed before distinguishing lengths are examined. If `H` is chosen after these results are seen, record that the similarity metrics are descriptive, not a pre-registered test.
5. Form a hypothesis from the observed distributions and design tailored follow-up simulations.
