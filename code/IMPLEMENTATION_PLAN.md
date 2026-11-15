# Implementation Plan: Shortest Distinguishing Strings

Status: approved design, not yet implemented. Written November 14, 2026.

## 1. Goal

For every unordered pair of DFAs in one generated batch, compute:
- the length of the shortest string accepted by exactly one DFA, and that string (the "witness"); or
- that the two DFAs are equivalent.

Also compute per-DFA statistics: the number of reachable states and the minimal-DFA size. The analysis needs these because the generator does not guarantee reachability or minimality (see `time-sensitive.md`).

This plan covers the core algorithm, the loader, the per-DFA statistics, the tests and the batch driver. **Out of scope:** the generator (`data/DFA_Generator.py`, a separate approved plan), analysis and plots, and comparisons across batches.

## 2. Decisions already made (do not reopen)

| Topic | Decision |
|---|---|
| Pairing | All unordered pairs `i < j` **within one batch** (one alphabet size, one state count, one run). No self-pairs and no cross-batch pairs. |
| Output | Save the length **and** the witness for every pair. Equivalent pairs get `null` for both. |
| Witness choice | The lexicographically smallest shortest witness, with symbols ordered as in the manifest's alphabet. This follows from BFS that expands symbols in manifest order (§5). |
| Witness encoding | A JSON list of symbol strings, e.g. `["1", "10", "0"]`. Never a concatenated string: symbols can be multi-character (`"10"`). |
| Per-DFA stats | Save the reachable-state count and the minimal-DFA size for every DFA. Raw samples are never modified. |
| Results location | `data/alphabet_<A>/states_<S>/<run_id>/pairs/<results_id>/`. Never overwrite an existing `<results_id>`. |
| Input format | Not final, because the generator isn't written. Everything depends on one small loader module (§4), which is adapted when the generator's format is fixed. |
| Alphabet mismatch | Log an error and **stop the run**. Never skip the pair and continue. |
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
```

**Import gotcha:** do not make `code/` itself a package or import it as `code`, because that name shadows the standard-library `code` module. The modules are top-level siblings inside `code/`:
- Tests run from the repo root with `python -m unittest discover -s code/tests -t code`, which puts `code/` on `sys.path`.
- `run_pairs.py` gets `code/` on the path automatically when run as a script. Its first cell should also insert its own directory into `sys.path`, so interactive sessions with a different working directory still work.

## 4. Loader (`loader.py`)

The only code that knows the on-disk format. Everything else uses these types:

```python
@dataclass(frozen=True)
class DFA:
    id: str                        # record ID from the batch
    delta: tuple[tuple[int, ...], ...]   # delta[state][symbol_index] -> state
    accept: tuple[bool, ...]       # accept[state]
    initial: int = 0

@dataclass(frozen=True)
class Batch:
    run_dir: Path
    alphabet: tuple[str, ...]      # explicit symbol order from manifest.json
    n_states: int
    dfas: tuple[DFA, ...]
    manifest: dict                 # raw manifest, carried into results provenance
    input_sha256: dict[str, str]   # sha256 of manifest.json and dfas.jsonl.gz

def load_batch(run_dir: Path) -> Batch: ...
```

`load_batch` reads `manifest.json` and `dfas.jsonl.gz` and maps their fields onto these types. Field names are assumed for now and **must be checked against the generator** once it exists. Put the field-name mapping in one clearly marked place.

The loader also runs cheap checks. Any failure gets logged with the record ID, then raises; it never silently skips.
- Every row of `delta` has length `len(alphabet)`. A wrong length counts as an **alphabet mismatch**: raise `AlphabetMismatchError` (defined in `loader.py`).
- Every destination is in `range(n_states)`, and `len(accept) == n_states == len(delta)`.
- `initial` is in range, and record IDs are unique.

## 5. Core algorithm (`distinguish.py`)

```python
@dataclass(frozen=True)
class Result:
    length: int | None             # None means equivalent
    witness: tuple[int, ...] | None   # symbol indices; convert to strings at write time

def shortest_distinguishing(a: DFA, b: DFA, n_symbols: int) -> Result: ...
```

Steps:
1. If `len` of any row in `a.delta` or `b.delta` is not `n_symbols`, log an error and raise `AlphabetMismatchError`. This guards against the function being called outside the loader.
2. Run BFS over state pairs, starting from `(a.initial, b.initial)` at depth 0. Mark pairs as visited **when they are enqueued**. Store a parent pointer `(previous_pair, symbol_index)` for each pair. A flat list indexed `p * n_b + q` is faster than a dict.
3. When a pair `(p, q)` is dequeued: if `a.accept[p] != b.accept[q]`, rebuild the witness from the parent pointers and return `Result(depth, witness)`.
4. Otherwise, for `s` in `range(n_symbols)` **in order**, enqueue `(a.delta[p][s], b.delta[q][s])` if it hasn't been visited.
5. If the queue empties, return `Result(None, None)`.

Why the witness is lexicographically smallest: BFS dequeues pairs depth by depth. Within a depth, pairs come out in the lexicographic order of their (lexicographically smallest) access strings, provided symbols are expanded in index order and pairs are marked visited at first enqueue. So the first mismatching pair dequeued gives the smallest shortest witness.

Cost: O(|Σ|·n₁·n₂) time and O(n₁·n₂) memory per pair.

Optional extension, needed by §6: `shortest_distinguishing_from(a, p0, b, q0, n_symbols)`, which starts from any pair of states. `shortest_distinguishing` calls it with the initial states.

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
2. Create `run_dir / "pairs" / results_id`. The default `results_id` is a UTC timestamp `YYYYmmddTHHMMSSZ`. If the directory already exists, log an error and raise; never overwrite. Write to a temporary sibling directory and rename it into place at the end, so a crashed run leaves no partial directory that looks complete.
3. Compute stats for every DFA. Write `dfa_stats.jsonl.gz`, one line per DFA:
   `{"id": ..., "n_states": S, "reachable": R, "minimal": M}`.
4. For every `i < j` in batch order, call `shortest_distinguishing`. Stream each result into `pairs.jsonl.gz`, one line per pair:
   `{"a": id_i, "b": id_j, "length": L | null, "witness": ["sym", ...] | null}`.
   Convert witness indices to symbol strings using `batch.alphabet`.
5. Write `manifest.json` with:
   - `results_id`, the run directory, the input file hashes, and the input manifest's alphabet and state count;
   - the pairing scheme (`"all unordered within-batch pairs, i<j in batch order"`), the expected and actual pair counts (`n·(n−1)/2`; 124,750 for n = 500), and the DFA count;
   - counts of equivalent pairs and length-0 pairs;
   - the repo git commit, a dirty-tree flag, the Python version, start and end timestamps, and the elapsed time.
6. Log progress every few thousand pairs. Any exception aborts the run, including `AlphabetMismatchError`.

## 8. Driver (`run_pairs.py`, `# %%` cells)

Keep the cells thin: all logic lives in the modules.
1. **Setup:** imports, logging configuration, and the `sys.path` insert from §3.
2. **Config:** `RUN_DIR` (one batch run directory) and an optional `RESULTS_ID`.
3. **Run:** `out = pairs.run_batch(RUN_DIR, RESULTS_ID)`.
4. **Quick checks (read-only):** load the output and print the pair count, the fraction equivalent, a length histogram (including 0), and the distribution of `minimal` sizes.

Final result sets should come from a fresh session or `python code/run_pairs.py`, not from a kernel with cells run out of order.

## 9. Tests (`code/tests/`)

Run all tests with `python -m unittest discover -s code/tests -t code`.

`helpers.py` provides: a `make_dfa(delta, accept)` builder; `random_dfa(rng, n, k)` for tiny random DFAs (no DeepDFA dependency); a brute-force oracle that lists every symbol sequence in shortlex order up to a bound and returns the first disagreement; and `write_synthetic_batch(tmp_dir, dfas, alphabet)`, which writes files in the loader's assumed format.

**`test_distinguish.py`**
- Hand-made cases: identical DFAs (equivalent); DFAs that differ on the empty string (length 0, witness `()`); equivalent DFAs with different state counts (a minimal DFA and a padded copy with redundant or unreachable states); a pair whose only difference needs a long string, e.g. "length ≡ 0 mod n" versus "mod m".
- Brute-force check: thousands of random pairs with 1–4 states and 1–3 symbols, seeded. The length **and the exact witness** must match the shortlex-first disagreement from the oracle. Equivalence must match "no disagreement up to n₁·n₂" (a sufficient bound).
- Witness validity: running the witness on both DFAs gives different acceptance, and `len(witness) == length`.
- Symmetry: swapping `a` and `b` gives the same length and witness.
- Multi-character symbols: with an 11-symbol alphabet, a witness containing symbol index 10 converts to `"10"`, not `"1", "0"`.
- A row of the wrong width raises `AlphabetMismatchError`.

**`test_dfa_stats.py`**
- Hand-made DFAs with unreachable states and with merged-equivalent states.
- Cross-check: `minimal_size` equals the number of equivalence classes of reachable states, computed with `shortest_distinguishing_from` on every pair of reachable states. Run this on many random small DFAs.

**`test_loader.py`**
- Round trip: write a synthetic batch, load it, and get equal DFAs and alphabet.
- Each validation error from §4 raises, and the log message names the record ID.

**`test_pairs.py`**
- End to end on a synthetic batch of about 10 DFAs in a temp directory: pair count is `n(n−1)/2`; every pair matches a direct `shortest_distinguishing` call; the manifest counts are consistent; the stats file has one line per DFA.
- A second run with the same `results_id` raises and leaves the first output unchanged.

## 10. Performance check

After the tests pass, time `run_batch` on a synthetic batch of 500 random DFAs at the largest planned state count and alphabet size. Use `random_dfa`, or the real generator if it exists. Record the result in the session log.

An earlier in-memory benchmark compared 19,900 pairs in about 0.1 s on easy random inputs, so 124,750 pairs should be fine. Equivalent or near-equivalent pairs are the worst case. If the full batch takes more than a few minutes, report back before optimizing.

## 11. Done when

- All tests pass with the command in §9.
- `run_pairs.py` runs end to end on a synthetic batch and produces the §7 layout.
- `time-sensitive.md` is updated: the algorithm is implemented, the loader field names are provisional until the generator is written, and the next steps are revised.
- A session log is in `agentLogs/` following the README convention.

## 12. Open items for later (not blockers)

- Confirm the loader field names against `data/DFA_Generator.py` once it is written.
- Pairs within one batch share DFAs, so the 124,750 results are not independent samples. The analysis plan must account for this, e.g. by subsampling disjoint pairs. The saved pair IDs make that possible without recomputing.
- Whether `data/` result files are committed to git or ignored is undecided.
