# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Research question: for two non-equivalent DFAs, how long is the shortest string accepted by exactly one of them? DFAs are generated with the DeepDFA submodule across state counts and alphabet sizes. The plan is an exploratory run, then a hypothesis, then targeted simulations. No experiment code, datasets or results exist yet.

**Read `time-sensitive.md` first.** It holds current status, the approved generator plan and next steps, and it is the authority on what to do next.

## Repository conventions (from README)

- Status and next steps go in `time-sensitive.md`; update it when status changes. Keep `README.md` for stable info.
- Generated DFAs, result files and visualizations go in `/data`.
- Experiment, test and analysis code goes in `/code`. Exception: the approved generator lives at `data/DFA_Generator.py`.
- **Every session must add a log to `/agentLogs`** named `Claude_YYYY-MM-DD_HH-MM-SS_<purpose>.md` (America/Chicago time). Summarize what changed, why, which files were touched, checks run and outstanding work. Follow the format of the existing `GPT_*` logs.
- Do not modify the `DeepDFA/` submodule. Import from it.

## Setup

DeepDFA is a git submodule (https://github.com/whitemech/DeepDFA) and may not be checked out:

    git submodule update --init

Earlier sessions inspected revision `e74c5f5b7371952060d7b2abfae29b42fba784ce` and used Python 3.12.2. There is no build, lint or test tooling yet.

## DeepDFA generator: known issues

- `DeepDFA/Random_DFA.py` defines `Random_DFA(number_of_states, number_of_symbols)`. It only needs the stdlib `random`, not PyTorch or Pythomata. Seed `random` before each sample for reproducibility.
- State 0 is the implicit initial state. Transitions are a dict keyed by symbol strings (`"0"`, `"1"`, … `"10"`). Acceptance is a list of flags.
- Sampling is **not uniform**. It forces a forward edge from each state except the last, then fills the other transitions at random. Reachability and minimality are not guaranteed. Keep raw samples (no minimization or rejection); equivalence is handled at comparison time.
- The concatenated `alphabet` attribute and the character-based acceptance helper break at 11 or more symbols (`"012345678910"`). Use explicit symbol lists and symbol sequences instead.
- Upstream `.pckl` samples pickle `__main__.Random_DFA`, so they are awkward to load elsewhere. Don't use pickle for project data.

## Data format (approved)

    data/alphabet_<A>/states_<S>/<run_id>/
      manifest.json   # explicit alphabet + column order, state count, sample count,
                      # generation params, seed scheme, Python version, DeepDFA commit
      dfas.jsonl.gz   # one DFA per line: id, seed, initial state,
                      # compact transition table, acceptance flags

There are 500 DFAs per (alphabet size, state count) combination. Never overwrite an existing run directory. Before bulk generation, validate transition completeness, destination ranges, acceptance length, seed reproducibility and serialization round trips.

## Distinguishing-length algorithm

- Use BFS over the product automaton's state pairs, starting at (0, 0) and stopping at the first pair whose acceptance flags differ. That BFS depth is the shortest distinguishing length. If BFS finishes with no mismatch, the DFAs are equivalent. Never enumerate strings.
- Cost per pair is O(|Σ|·n₁·n₂) time and O(n₁·n₂) memory. Pair count grows quadratically: 500 DFAs give 124,750 unordered pairs per batch.
- Keep length-0 results (the empty string distinguishes about half of random pairs). Report the conditional distribution of positive lengths separately as a supplement, not a replacement.
