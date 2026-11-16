# Combine SDS/similarity figures

Agent GPT; November 15, 2026, America/Chicago.

User requested easier visual comparison with four combined files. Updated `dataviz/sds_similarity.py` to produce agreement/Jaccard by alphabet (four panels each, 2x2) and by generated state count (three panels each, one row). Kept colors, bins, conditional means, axes ranges, and data selection unchanged. Default output is `dataviz/figures/sds_vs_similarity/`. Preserved all fourteen individual SVGs plus their CSV/provenance in `individual/` beneath that directory.

Updated the parameter notebook's output directory and display loop, README figure links, and project status. Regenerated from saved H=5 comparisons; no experiment calculations or generation. Explained to the user that the positive trend is expected in part from the mathematical agreement constraint, and that binned mean curves alone do not quantify pairwise correlation strength.

Validation: executed the plotting workflow against all twenty saved batches. Checked the four SVG exports and panel counts, notebook schema and code compilation, provenance/script hash, and unchanged bin-table contents against the preserved original. No repository test files changed or test suite run. Existing unrelated changes and archives preserved.
