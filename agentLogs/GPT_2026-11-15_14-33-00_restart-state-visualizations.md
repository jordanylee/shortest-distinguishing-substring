# Restart visualization workspace with two state-distribution figures

User requested a fresh start, archival of the existing visualization code and outputs, and only two new figures: reachable and minimal state distributions across all twenty configurations.

Moved the entire existing `dataviz/` directory to `archive/dataviz_2026-11-15_14-30-09/` using checked absolute paths inside the workspace and no overwrite. Recorded and verified SHA256 hashes for all 57 files in the archive's companion JSON inventory. Raw experimental data, experiment code, and existing user changes elsewhere were preserved.

Created a small replacement `dataviz/` workspace:

- `state_distributions.py`: loads explicit saved per-DFA statistics and generates two figures, with shared colors/legend and the requested axis labels.
- `State_Distributions.ipynb`: parameters, script call, and display of the two figures. Saved cell outputs are cleared.
- `figures/reachable_states.png` and `.svg`; `minimal_states.png` and `.svg`.
- `figures/state_distributions.csv` and `provenance.json`: counts/percentages and 80 input hashes.
- `README.md`, `requirements.txt`: concise usage and archive links.

Inputs: source `2026-11-15_19-36-35-433280_UTC`, comparison statistics `2026-11-15_19-55-50-157162_UTC`; alphabet sizes 2/3/4/5 and generated state counts 10/15/20/25/30, 500 DFAs per configuration. The comparison run uses H=5, but state statistics do not depend on that horizon; no pair scores were read or calculated.

Executed the script and visually inspected both figures. Checked complete manifests, 500 unique matched source/stat IDs per configuration, valid minimal <= reachable <= generated sizes, saved histogram equality, source hashes, and normalization. All forty distributions (two statistics times twenty configurations) total 500 DFAs and 100%. Verified exactly two PNG/SVG figure pairs, current script hash, notebook schema and compiled code cells, and all archived file hashes. Updated the visualization paragraph in time-sensitive.md to point to the new workspace and archive. No experiment code or test files were changed.
