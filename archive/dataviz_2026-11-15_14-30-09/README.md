# DFA visualizations

Open [DFA_Visualizations.ipynb](DFA_Visualizations.ipynb), edit its parameter cell, and run all cells. It works when Jupyter starts from the repository root or `dataviz/`. All logic lives in [analyze.py](analyze.py).

Alternatively, from the repository root:

```powershell
python dataviz/analyze.py
```

Dependencies are listed in `requirements.txt`. The default run reads the canonical source and the explicit H=4 result ID in the script; it never generates DFAs or recomputes comparisons. H=3 results are not required. CLI options `--source-id`, `--h4-id`, and `--output` select alternatives. Repeating a visualization run replaces its own figure/table exports.

The report and figure gallery are in [outputs/2026-11-15_17-55-16-095569_UTC/REPORT.md](outputs/2026-11-15_17-55-16-095569_UTC/REPORT.md). Each figure has PNG and SVG versions. `tables/` contains distributions, bin counts, per-DFA summaries, sensitivity checks, and concrete anomaly IDs. `provenance.json` records input hashes and software versions.

Read [FINDINGS.md](FINDINGS.md) for the initial interpretation and follow-up ideas.

The user's `dataviz/` destination takes precedence over the repository's usual `code/` and `data/` locations for this deliverable. Raw inputs remain in `data/`.

Interpretation: these are descriptive comparisons of dependent pairs from a biased generator. Equivalent pairs are separate from finite SDS. Similarity is bounded by the saved horizon and cannot establish language equivalence. Accepting-state fraction includes all raw states; acceptance mass uses the bounded word distribution. No confidence intervals treating pairs as independent are supplied.

The trimmed gallery contains 13 figures. Minimal-size, unreachable-percentage, tail-concentration, and horizon-change plots have been removed. Similarity distributions contain only two histograms. Mean SDS bars show numerical values.

`diagnostics.py` checks agreement bin assignment and the 10-state Jaccard dips. Agreement bins use exact integer arithmetic because floating-point edges caused artificial oscillations. Tables retain original/corrected histogram counts, exact score counts, anomaly pairs, and sensitivity checks.
