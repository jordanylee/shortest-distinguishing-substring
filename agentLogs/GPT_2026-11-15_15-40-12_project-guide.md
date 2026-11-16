# Project guide

The user invoked ask-matt and requested a Markdown guide explaining the growing collection of scripts. Read the supplied/local routing skill and treated the clear documentation request as a bounded inventory task. Inspected active notebooks, Python module responsibilities, CLI arguments, saved report locations, repository conventions, plotting documentation, and upstream/archive layout.

Created `PROJECT_GUIDE.md` in the repository root. It starts with a task-to-entry-point table, then explains folders, runnable scripts versus imported calculation modules, source/result identities, the data directory layout, output records, common commands, metric terminology, every active test module, documentation, DeepDFA, and historical exports. Included the newer below-half filtering and experiment-specific comparison-table scripts/reports discovered during the inventory. Explained independent notebook/script settings and that current plotting scripts read within-batch results, not optional cross-state outputs.

Added a prominent link immediately below the README title. Preserved other ongoing changes and left all scripts, notebooks, experiment inputs/results, figure exports, and historical files in place. No calculations or generation were run, and no dependencies were installed.

Validation: checked that all 62 local Markdown links resolve and that all 33 active Python/notebook files under code/, code/tests/, data/, and dataviz/ are covered by the guide. `git diff --check -- README.md PROJECT_GUIDE.md` passed. No test-suite rerun was needed for this documentation-only change.
