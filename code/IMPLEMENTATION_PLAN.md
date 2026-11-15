# Implementation Plan: Shortest Distinguishing Strings

Status: approved design, not yet implemented. Written November 14, 2026, and revised the same day after the generator and the first DFA batches were merged.

Related documents:
- `time-sensitive.md`, section "Approved Exploratory Testing Plan": the experiment-level decisions this plan implements.
- `similarity-metrics.md`: a separate planned module, `code/similarity_metrics.py`, that scores the same pairs. It should reuse this plan's loader (§4) and pair keys (§7).
- `data/DFA_Generator.py`: the generator, whose output format §4 reads.

## 1. Goal

For every unordered pair of DFAs in one generated batch, compute:
- the length of the shortest string accepted by exactly one DFA, and that string (the "witness"); or
- that the two DFAs are equivalent.

Also compute per-DFA statistics: the number of reachable states and the minimal-DFA size. The analysis needs these because the generator does not guarantee reachability or minimality.

This plan covers the loader, the core algorithm, the per-DFA statistics, the tests and the batch driver. **Out of scope:** changes to the generator, the similarity metrics, analysis and plots, and comparisons across batches.

## 2. Decisions already made (do not reopen)

| Topic | Decision |
|---|---|
| Pairing | All unordered pairs `i < j` **within one batch** (one alphabet size, one state count, one run). No self-pairs and no cross-batch pairs. |
| Canonical input | Run `2026-11-15_00-36-37-375402_UTC`: 6 batches, alphabets {2, 3} × states {10, 20, 30}, 500 DFAs each. Run `2026-11-15_00-30-21-627385_UTC` has **identical records** (same master seed). Don't process it, or results get double-counted. |
| Output | Save the length **and** the witness for every pair. Equivalent pairs get `null` for both and are never given length 0. |
| Witness choice | The lexicographically smallest shortest witness, with symbols ordered as in the manifest's `alphabet`. This follows from BFS that expands symbols in manifest order (§5). |
| Witness encoding | A JSON list of symbol strings, e.g. `["1", "10", "0"]`. Never a concatenated string: symbols can be multi-character (`"10"`). |
| Per-DFA stats | Save the reachable-state count and the minimal-DFA size for every DFA. Raw samples are never modified. |
| Results location | `data/alphabet_<A>/states_<S>/<run_id>/pairs/<results_id>/`. Never overwrite an existing `<results_id>`. |
| Results storage | Result files are **gzip-compressed by default** (about 35 MB uncompressed across six batches) and **committed to git**, like the DFA batches. |
| Input access | Only `code/loader.py` knows the on-disk format. Other modules, including the planned similarity metrics, go through it. |
| Alphabet mismatch | Log an error and **stop the run**. Never skip the pair and continue. Within one batch the alphabet is identical by construction, so a mismatch means corrupted data or a bug. (`similarity-metrics.md` plans to line up columns when two alphabets order symbols differently; that never applies within a batch, so it doesn't conflict.) |
| Code layout | Logic lives in plain importable modules. The driver is a notebook-style `# %%` file that only sets parameters and calls those modules. |
| Dependencies | Python 3.12 standard library only. Tests use `unittest`, which `pytest` can also run. |

## 3. Files

```
code/
  IMPLEMENTATION_PLAN.md   # this file
  loader.py                # module: reads one batch (§4), the only format-specific code
  distinguish.py           # module: product-automaton BFS (§5)
  dfa_stats.py             # module: reachable count and minimal size (§6)
  pairs.py                 # module: runs all pairs for a batch and writes results (§7)
  run_pairs.py             # "# %%" driver: config cell + calls into pairs.py (§8)
  tests/
    __init__.py
    helpers.py             # small DFA builders, brute-force oracle, synthetic batch writer
    test_distinguish.py
    test_dfa_stats.py
    test_loader.py
    test_pairs.py
    test_real_data.py      # checks against the committed canonical run (§9)
```

**Import gotcha:** do not make `code/` itself a package or import it as `code`, because that name shadows the standard-library `code` module. The modules are top-level siblings inside `code/`:
- Tests run from the repo root with `python -m unittest discover -s code/tests -t code`, which puts `code/` on `sys.path`.
- `run_pairs.py` gets `code/` on the path automatically when run as a script. Its first cell should also insert its own directory into `sys.path`, so interactive sessions with a different working directory still work.

Do not import from `data/DFA_Generator.py`. It's a notebook companion script in `data/` and would need path workarounds. Mirror its validation logic in the loader instead (§4).

## 4. Loader (`loader.py`)

### On-disk format (from `data/DFA_Generator.py`, `schema_version` 1)

A run directory `data/alphabet_<A>/states_<S>/<run_id>/` contains:
- `manifest.json`, with the fields used here:
  - `schema_version` (1) and `status` (`"complete"`);
  - `run_id`, `state_count`, `alphabet_size` and `alphabet` (list of symbol strings, which is also the column order);
  - `sample_count`, `initial_state` (0) and `batch_file` (a file name in the same directory).
- The batch file named by `batch_file`, e.g. `dfas_alphabet-3_states-10_count-500_<timestamp>.jsonl`. **Plain `.jsonl` by default; `.jsonl.gz` if the name ends in `.gz`.** Detect compression from the file name. The older run's manifest has no `compression` field, so don't rely on it.
- One JSON object per line:
  ```json
  {"id": 0, "seed": "6121…", "initial_state": 0,
   "transitions": [[4,3,4], [4,9,9], …], "acceptance": [true, false, …]}
  ```
  `id` is a zero-based **integer**, unique within its batch. `transitions[state][alphabet_column]` is the destination state, and `acceptance[state]` is a boolean.

### Interface

```python
@dataclass(frozen=True)
class DFA:
    id: int
    delta: tuple[tuple[int, ...], ...]   # delta[state][symbol_index] -> state
    accept: tuple[bool, ...]             # accept[state]
    initial: int

@dataclass(frozen=True)
class Batch:
    run_dir: Path
    run_id: str
    alphabet: tuple[str, ...]      # manifest["alphabet"], in column order
    n_states: int
    dfas: tuple[DFA, ...]          # in file order
    manifest: dict                 # raw manifest, carried into results provenance
    input_sha256: dict[str, str]   # sha256 of manifest.json and the batch file

class AlphabetMismatchError(ValueError): ...
class BatchFormatError(ValueError): ...

def load_batch(run_dir: Path) -> Batch: ...
```

Map the JSON fields to the dataclasses in one clearly marked block. Then a change to the format only needs edits there.

### Checks

Each failure is logged with the run directory and record `id`, then raises; nothing is ever silently skipped. These mirror `validate_record` in the generator.
- The manifest has `status == "complete"` and `schema_version == 1`. Otherwise raise `BatchFormatError`; an incomplete run may hold a partial batch.
- `len(alphabet) == alphabet_size`.
- The number of records equals `sample_count`, and the record IDs are unique.
- For every record:
  - `len(transitions) == len(acceptance) == state_count`;
  - every destination is an `int` in `range(state_count)`;
  - every acceptance flag is a `bool`;
  - `initial_state` is in range.
- Every row of `transitions` has length `len(alphabet)`. A wrong length counts as an alphabet mismatch: raise `AlphabetMismatchError`.

## 5. Core algorithm (`distinguish.py`)

```python
@dataclass(frozen=True)
class Result:
    length: int | None                # None means equivalent
    witness: tuple[int, ...] | None   # symbol indices; convert to strings at write time

def shortest_distinguishing(a: DFA, b: DFA, n_symbols: int) -> Result: ...
def shortest_distinguishing_from(a: DFA, p0: int, b: DFA, q0: int, n_symbols: int) -> Result: ...
```

`shortest_distinguishing` calls `shortest_distinguishing_from(a, a.initial, b, b.initial, n_symbols)`.

Steps:
1. If any row in `a.delta` or `b.delta` doesn't have `n_symbols` entries, log an error and raise `AlphabetMismatchError`. This guards against the function being called outside the loader.
2. Run BFS over state pairs, starting from `(p0, q0)` at depth 0. Mark pairs as visited **when they are enqueued**. Store a parent pointer `(previous_pair, symbol_index)` for each pair. A flat list indexed `p * n_b + q` is faster than a dict.
3. When a pair `(p, q)` is dequeued: if `a.accept[p] != b.accept[q]`, rebuild the witness from the parent pointers and return `Result(depth, witness)`.
4. Otherwise, for `s` in `range(n_symbols)` **in order**, enqueue `(a.delta[p][s], b.delta[q][s])` if it hasn't been visited.
5. If the queue empties, return `Result(None, None)`.

Why the witness is lexicographically smallest: BFS dequeues pairs depth by depth. Within a depth, pairs come out in the lexicographic order of their (lexicographically smallest) access strings, provided symbols are expanded in index order and pairs are marked visited at first enqueue. So the first mismatching pair dequeued gives the smallest shortest witness.

Cost: O(|Σ|·n₁·n₂) time and O(n₁·n₂) memory per pair.

## 6. Per-DFA statistics (`dfa_stats.py`)

```python
def reachable_states(d: DFA) -> frozenset[int]: ...   # BFS from d.initial
def minimal_size(d: DFA, n_symbols: int) -> int: ...  # Moore partition refinement on the reachable part
```

- `minimal_size` counts states in the minimal complete DFA, including any dead/sink state that is reachable. Moore's algorithm takes O(|Σ|·n²) in the worst case, which is fine at these sizes.
- Edge case: if every reachable state has the same acceptance flag, the minimal size is 1.

## 7. Batch runner (`pairs.py`)

```python
def run_batch(run_dir: Path, results_id: str | None = None) -> Path: ...
```

1. `load_batch(run_dir)`.
2. Create `run_dir / "pairs" / results_id`.
   - The default `results_id` is a UTC timestamp in the generator's style, `YYYY-mm-dd_HH-MM-SS-ffffff_UTC`.
   - If the directory already exists, log an error and raise; never overwrite.
   - Write into a temporary sibling directory `<results_id>.part` and rename it into place at the end, as the generator does with `.part` files. A crashed run then never looks complete.
3. Compute stats for every DFA. Write `dfa_stats.jsonl.gz`, one line per DFA in batch order:
   `{"id": 0, "n_states": S, "reachable": R, "minimal": M}`.
4. For every `i < j` in batch order, call `shortest_distinguishing`. Stream each result into `pairs.jsonl.gz`, one line per pair:
   `{"a": id_i, "b": id_j, "length": L | null, "witness": ["sym", ...] | null}`.
   - Convert witness indices to symbol strings using `batch.alphabet`.
   - `(a, b)` with `a < b` is the **pair key**. Document it in the manifest so `similarity_metrics` results can be joined on the same key.
   - Files are gzip-compressed (see §2). A `compress=False` flag exists for debugging only.
5. Write `manifest.json` with:
   - `schema_version`, `status: "complete"` (written last) and `results_id`;
   - the source `run_id`, the run directory, the input file hashes, `alphabet` and `state_count`;
   - the pairing scheme (`"all unordered within-batch pairs, a<b by id"`), the pair-key definition, and the expected and actual pair counts (`n·(n−1)/2`; 124,750 for n = 500), plus the DFA count;
   - counts of equivalent pairs and length-0 pairs, and the maximum finite length;
   - the repo git commit, a dirty-tree flag, the Python version, start and end timestamps, and the elapsed time.
6. Log progress every few thousand pairs. Any exception aborts the run, including `AlphabetMismatchError` and `BatchFormatError`.

Also provide `run_all(run_id: str, data_root: Path) -> list[Path]`. It finds every `data/alphabet_*/states_*/<run_id>/` directory and calls `run_batch` on each, using one shared `results_id`.

## 8. Driver (`run_pairs.py`, `# %%` cells)

Keep the cells thin: all logic lives in the modules.
1. **Setup:** imports, logging configuration, and the `sys.path` insert from §3.
2. **Config:** `RUN_ID = "2026-11-15_00-36-37-375402_UTC"` (the canonical run), an optional `RESULTS_ID`, and an optional filter on alphabet sizes and state counts.
3. **Run:** `outs = pairs.run_all(RUN_ID, DATA_ROOT, ...)`.
4. **Quick checks (read-only):** for each output, print the pair count, the equivalent count and rate, a length histogram (including 0), the maximum length, and the distribution of `minimal` sizes.

Final result sets should come from a fresh session or `python code/run_pairs.py`, not from a kernel with cells run out of order.

## 9. Tests (`code/tests/`)

Run all tests with `python -m unittest discover -s code/tests -t code`.

`helpers.py` provides:
- a `make_dfa(delta, accept, id=0)` builder;
- `random_dfa(rng, n, k)` for tiny random DFAs (no DeepDFA dependency);
- a brute-force oracle that lists every symbol sequence in shortlex order up to a bound and returns the first disagreement;
- `write_synthetic_batch(tmp_dir, dfas, alphabet, compress=False)`, which writes a manifest and batch file **in the generator's exact format** (§4).

**`test_distinguish.py`**
- Hand-made cases:
  - identical DFAs (equivalent);
  - DFAs that differ on the empty string (length 0, witness `()`);
  - equivalent DFAs with different state counts, e.g. a minimal DFA and a padded copy with redundant or unreachable states;
  - a pair whose only difference needs a long string, e.g. "length ≡ 0 mod n" versus "mod m".
- Brute-force check: thousands of random pairs with 1–4 states and 1–3 symbols, seeded. The length **and the exact witness** must match the shortlex-first disagreement from the oracle. Equivalence must match "no disagreement up to n₁·n₂" (a sufficient bound).
- Witness validity: running the witness on both DFAs gives different acceptance, and `len(witness) == length`.
- Symmetry: swapping `a` and `b` gives the same length and witness.
- Multi-character symbols: with an 11-symbol alphabet, a witness containing symbol index 10 converts to `"10"`, not `"1", "0"`.
- A row of the wrong width raises `AlphabetMismatchError`.

**`test_dfa_stats.py`**
- Hand-made DFAs with unreachable states and with merged-equivalent states.
- Cross-check: `minimal_size` equals the number of equivalence classes of reachable states, computed with `shortest_distinguishing_from` on every pair of reachable states. Run this on many random small DFAs.

**`test_loader.py`**
- Round trip: write a synthetic batch, load it, and get equal DFAs and alphabet. Run this both plain and gzip.
- Each check in §4 raises, and the log message names the record `id`. Include a missing or incomplete `status`, a wrong `sample_count`, and an older-style manifest with no `compression` field (which must still load).

**`test_pairs.py`**
- End to end on a synthetic batch of about 10 DFAs in a temp directory:
  - the pair count is `n(n−1)/2`;
  - every pair matches a direct `shortest_distinguishing` call;
  - the manifest counts are consistent;
  - the stats file has one line per DFA.
- A second run with the same `results_id` raises and leaves the first output unchanged.

**`test_real_data.py`** (read-only; never writes into `data/`)
- All 6 canonical batches load and pass validation, each with 500 DFAs.
- The two committed runs load to identical DFAs, confirming the duplicate.
- Cross-check against GPT's benchmark log (`agentLogs/GPT_2026-11-14_18-44-44_existing-batch-runtime-benchmark.md`), computed in memory: alphabet 2 with 10 states has **37** equivalent pairs, and the other five batches have **0**. If these don't match, stop and report; don't adjust the test to fit.
- Brute-force check of a few hundred sampled real pairs, using the oracle up to a bound of the largest observed length + 1.

## 10. Performance check

GPT benchmarked these batches at about 0.5 s per batch of 124,750 pairs (lengths only, no witnesses, no file writing). After the tests pass, time `run_all` on the canonical run and record the result in the session log. Witnesses and writing will add overhead, but the full run should still take well under a minute. If it takes more than a few minutes, report back before optimizing.

## 11. Done when

- All tests pass with the command in §9.
- `run_pairs.py` has produced results for all 6 canonical batches under `.../2026-11-15_00-36-37-375402_UTC/pairs/<results_id>/`, and they are committed.
- `time-sensitive.md` is updated: the algorithm is implemented, results exist, the observed equivalent counts and maximum lengths are recorded, and next steps are revised.
- A session log is in `agentLogs/` following the README convention.

## 12. Open items for later (not blockers)

- Pairs within one batch share DFAs, so the 124,750 results are not independent samples (see the "Approved Exploratory Testing Plan" in `time-sensitive.md`). The analysis plan must account for this, e.g. with independently seeded batches or subsampling of disjoint pairs. The saved pair keys make that possible without recomputing.
- When `similarity_metrics.py` is implemented, it should import `loader.load_batch` rather than parsing files itself.
