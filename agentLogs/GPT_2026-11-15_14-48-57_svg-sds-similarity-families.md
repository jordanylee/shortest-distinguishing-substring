# SVG exports and curated SDS/similarity families

Agent: GPT. November 15, 2026, America/Chicago.

## Changes

- Changed `dataviz/state_distributions.py` to export SVG only; regenerated reachable/minimal state SVGs and removed exactly their two active PNG exports. Updated `State_Distributions.ipynb` to display SVGs. Archived figures and scripts were preserved.
- Added `dataviz/sds_similarity.py` and parameter notebook `SDS_Similarity.ipynb`. Each metric family has four alphabet-specific figures (five state-count lines each) and three state-specific figures at 10/20/30 (four alphabet lines each). Colors use the existing blue/red/green/purple alphabet families and state shades.
- Similarity is on x; y is mean finite SDS within fixed-width similarity bins (default 0.05). X uses observed bin mean. Empty bins break lines; equivalent pairs are excluded and zero-length distinctions retained. All fourteen plots share axis ranges. Exported CSV includes every bin, counts, means and SDS ranges.
- Updated `dataviz/README.md` with all SVG links, interpretation and usage; added a current-status note to `time-sensitive.md`.

## Data and validation

Used source `2026-11-15_19-36-35-433280_UTC` and comparisons `2026-11-15_19-55-50-157162_UTC` at saved H=5, twenty configurations (alphabets 2–5; states 10/15/20/25/30). Read every saved pair exactly once per configuration: 2,495,000 rows total. No generation, BFS or metric calculation ran.

Both scripts completed. Loader checks source hashes, complete result manifests, common horizon, unique ordered pair keys with source-scoped IDs, complete pair counts, SDS histograms/equivalence counts, metric ranges and necessary horizon constraints. Checked all CSV bin counts against finite-pair denominators, all sixteen SVGs as XML, absence of active PNGs, current analysis script hash, and notebook schema/code compilation. Notebook kernels were not executed. No repository tests added or run.

Outputs: `dataviz/figures/` contains sixteen SVGs, the existing state CSV/provenance, and new `sds_similarity_bins.csv` / `sds_similarity_provenance.json`. Preserved unrelated existing working-tree changes, archived files, generated data, and dirty DeepDFA submodule.
