# Shortest Distinguishing String

## 1. Summary

We are answering the question: **For two non-equivalent DFAs, how long does the shortest string distinguishing their languages tend to be?** A distinguishing string is accepted by exactly one of the two deterministic finite automata (DFAs).

We will use DeepDFA to generate a large collection of DFAs, varying the number of states and alphabet size. An initial exploratory run will empirically measure the distribution of shortest distinguishing string lengths. We will then form a hypothesis based on these observations and run more tailored simulations to investigate it.

## 2. Guidelines

- Put time-sensitive information, including current project status and next steps, in [time-sensitive.md](time-sensitive.md).
- Store generated DFAs, result files, and data visualizations in `/data`.
- For every session, create a Markdown file in `/agentLogs`. Include the agent name (`GPT` or `Claude`), date, time, and basic project or purpose in the filename; for example, `GPT_2026-11-14_18-02-15_project-documentation.md`. Summarize the work performed with a focus on traceability: what changed, why, which files were affected, and any checks or outstanding work.
- Put code for running tests, experiments, and analysis in `/code`. DFA generation is handled through DeepDFA.
