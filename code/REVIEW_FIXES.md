# Fixes from Code Review of `d763ecf` and `5b8cdb2`

Status: **resolved** (November 14, 2026). A medium-level review of the loader, BFS, DFA stats,
batch runner and run notebook produced ten findings. A second pass checked each one against the
code, the data and two timings. Six were applied and four were declined. See
`agentLogs/Claude_2026-11-14_20-38-20_apply-review-fixes.md`.

None of the findings affected the committed canonical results. After the fixes, a rerun of all
six canonical batches in a scratch copy produced byte-identical `pairs.jsonl.gz` and
`dfa_stats.jsonl.gz` files.

Context for the triage: the full canonical run takes about 10 s, and every input comes from
this project's own generator. Guarding against hypothetical inputs or a cheap-to-redo failure
was weighed against that.

## Applied

| # | Finding | Change |
|---|---|---|
| 1 | A crashed run left an invisible `.part/` dir (gitignored). Only an explicit reuse of the same `results_id` collided; default ids are fresh timestamps. | `run_batch` removes `part_dir` on any exception (`try/except BaseException`) and re-raises. Startup cleanup and the cross-drive `relpath` change were not done (`relpath` only raises on Windows). |
| 3 | `find_run_dirs` called `int()` on unchecked dir suffixes, so a stray `alphabet_2_old/` broke `run_all` and the `skipUnless` import of `test_real_data`. | Regex match `^alphabet_(\d+)$` / `^states_(\d+)$`; non-matching dirs are skipped with a warning. |
| 4 | A JSONL line that is valid JSON but not an object raised `AttributeError`. | `load_batch` raises `BatchFormatError` with the line number. |
| 6 | Out-of-range start states silently mapped to a different pair key. | `shortest_distinguishing_from` checks start-state range and `len(accept) == len(delta)` and raises `ValueError`. |
| 7 | `_check_width` re-scanned both DFAs on every pair (about 40% of BFS time on alphabet 2 / states 30: 0.46 s vs 0.26 s). | New `check: bool = True` keyword on `shortest_distinguishing[_from]`. `run_batch` passes `check=False`, since `load_batch` already validated every row. |
| 10 | `done != expected_pairs` could never fire. | Deleted. A re-read of the gzip file was not added. |

## Declined

| # | Finding | Why not |
|---|---|---|
| 2 | `run_all` can leave a partial result set; a retry under a new id could double-count. | The fix is to delete the partial set and rerun (about 10 s). Analysis code should take an explicit `results_id` (as `time-sensitive.md` does) rather than glob `pairs/*`. A run-level manifest and resume logic is not worth the machinery. Revisit if runs become long. |
| 5 | Manifest field types are not checked (list manifest, `"alphabet": "012"`). | The generator always writes a dict manifest with a list alphabet (`data/DFA_Generator.py`). Purely hypothetical. |
| 8 | Reachability is computed twice per DFA. | Microseconds per batch. |
| 9 | The notebook quick-check re-parses all pair lines. | 1.4 s for all six batches. It also acts as an independent cross-check of the manifest. The divide-by-zero needs fewer than 2 DFAs, and batches are fixed at 500. |

## Tests

`python3.12 -m unittest discover -s code/tests -t code`: 32 tests, all pass (5 new):
- `test_pairs.test_failure_removes_part_dir`: a failure partway leaves no `.part/`, and the same id then succeeds.
- `test_pairs.test_find_run_dirs_skips_bad_names`
- `test_loader.test_non_object_record`
- `test_distinguish.test_start_state_range`
- `test_distinguish.test_check_false_matches`
