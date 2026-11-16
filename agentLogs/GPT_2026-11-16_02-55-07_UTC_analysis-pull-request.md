# Prepare analysis-to-main pull request

Agent GPT; November 16, 2026, 02:55:07 UTC (November 15 in America/Chicago).

User requested a PR from `analysis` to `main` with a careful explanation of the entire branch. Read PROJECT_GUIDE.md and inspected the complete comparison against freshly fetched `origin/main`, all nine existing branch commits, changed calculation/notebook/test code, saved manifests, reports, visualization exports, archived diagnostics, and preceding session logs. The branch was already pushed at `73ca55b`; its only local status entry was an untracked Python cache inside the unchanged DeepDFA submodule. No experiment or notebook configuration was modified for PR preparation.

## Scope documented in the PR

Cross-state runner/notebook integration with state-qualified endpoint identities; the cached-import `sort_ids` regression fix; strict below-half-accepting selection and report generation; original twenty-batch, twelve-batch cross-state, ten-batch filtered, and six-batch seed-20 experiments; archived H=4 diagnostics; curated SVG/notebook workflows; ten-figure presentation summary and supporting tables/provenance; project navigation and dated findings. The 48 saved experiment batches contain 6,506,715 pair rows, with the 263,215 filtered comparisons overlapping their full-sample baseline. The presentation summary covers the other 38 batches and 6,243,500 rows.

The PR description includes exact run IDs, figure organization, key findings and interpretive limits, reproduction commands, recommended review order, and explicit validation limitations. Existing BFS/similarity algorithms and the DeepDFA submodule revision are unchanged from main. The bulk of the branch is intentionally committed experiment data, exported figures, and archived analysis artifacts.

## Checks in this session

- Fetched origin, confirmed `analysis` and its upstream were initially identical, and found no existing open analysis-to-main PR using the GitHub connector.
- Ran `python -B -m unittest discover -s code/tests -t code`: 56 tests, 54 passed, 2 failed. Fresh-kernel execution, warm-kernel cross-state regression, calculation, source loading, strict-filter, and cross-state tests passed.
- `NotebookSourceTests.test_companion_cells_match_and_outputs_are_clear` fails because the committed notebook retains seed-20 / 5-10-15-state / H=5 configuration and execution outputs while its Python companion retains earlier source / 10-20-30-state / H=3 settings. The user's experiment settings and saved outputs were preserved; the PR explicitly reports this failure.
- `RealData.test_duplicate_run_identical` fails because historical duplicate source `2026-11-15_00-30-21-627385_UTC` is absent. Neither the test nor that fixture was added by this branch; the canonical six-batch dataset is present and its other real-data checks passed.
- Reconciled all 48 completed experiment manifests and their H=5 pair totals.
- Rehashed all 128 presentation provenance inputs: zero mismatches. Current presentation script hash matches its recorded provenance. All ten figure links and all supporting local links resolve.
- Checked the archived inventory: all 57 local snapshot files match their recorded SHA256 values. One Python bytecode cache is ignored by Git; all 56 non-cache snapshot files are tracked.
- Confirmed the DeepDFA gitlink matches main exactly. Its untracked runtime cache is excluded from the PR.

Only this session log was added as part of PR preparation. The PR is intended for review and merge through GitHub; main is not modified locally and no merge or automatic merge is requested.
