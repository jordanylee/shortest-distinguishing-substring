# Current Project Status

Last updated: November 14, 2026 (America/Chicago).

The project is at the initial setup and experiment-planning stage. DeepDFA is present as a Git submodule in `/DeepDFA`, and the `/data`, `/code`, and `/agentLogs` directories exist. The root README now records the research question, experimental approach, and repository guidelines.

No project experiment code, generated datasets, results, or visualizations are present in `/code` or `/data` yet. The exploratory run has not been carried out, and no empirical hypothesis has been formed.

## Next Steps

1. Inspect DeepDFA's generation workflow and determine how to generate and export DFAs into `/data`.
2. Define the exploratory experiment: state counts, alphabet sizes, sample sizes, pairing strategy, and random seeds.
3. Implement and validate code in `/code` to detect equivalent pairs and find shortest distinguishing strings for non-equivalent pairs.
4. Run the exploratory simulations and save results and visualizations in `/data`.
5. Form a hypothesis from the observed distributions and design tailored follow-up simulations.
