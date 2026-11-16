"""Execute the real notebook on temporary data; never write to project data/."""

import importlib.util
import importlib
import contextlib
import io
import json
import random
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.helpers import random_dfa, write_synthetic_batch

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "code" / "DFA_Comparisons.ipynb"
HAS_JUPYTER = all(importlib.util.find_spec(m) for m in ("nbformat", "nbclient", "ipykernel"))


class NotebookSourceTests(unittest.TestCase):
    def test_companion_cells_match_and_outputs_are_clear(self):
        notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        companion = (NOTEBOOK.with_suffix(".py")).read_text(encoding="utf-8")
        chunks = re.split(r"^# %%[^\n]*\n", companion, flags=re.M)[1:]
        self.assertEqual(len(chunks), len(notebook["cells"]))
        for chunk, cell in zip(chunks, notebook["cells"]):
            source = chunk.rstrip() + "\n"
            if cell["cell_type"] == "markdown":
                source = "\n".join(line[2:] if line.startswith("# ") else "" if line == "#" else line
                                   for line in source.splitlines()) + "\n"
            self.assertEqual(source, "".join(cell["source"]))
            if cell["cell_type"] == "code":
                self.assertEqual(cell["outputs"], [])
                self.assertIsNone(cell["execution_count"])


class NotebookWarmKernelTests(unittest.TestCase):
    def test_optional_cells_refresh_cached_pre_cross_state_modules(self):
        import cross_state
        import experiments

        def legacy_pair_record(a, b, alphabet, calculations, horizon):
            raise AssertionError("cached calculation must be refreshed")

        notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        # Exercise either cell directly, as users can rerun a single notebook cell.
        cells = [c for c in notebook["cells"] if c["cell_type"] == "code" and
                 any(name in "".join(c["source"]) for name in ("cross_preview =", "cross_result_dirs ="))]
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            for n in (10, 20, 30):
                write_synthetic_batch(
                    data / "alphabet_2" / f"states_{n}" / "warm",
                    [random_dfa(random.Random(n + i), n, 2, id=i) for i in range(2)],
                    ["0", "1"], run_id="warm")
            for cell in cells:
                source = "".join(cell["source"])
                with self.subTest(cell="preview" if "cross_preview =" in source else "run"):
                    scope = {"ENABLE_CROSS_STATE": True, "CROSS_RUN_ID": "warm", "DATA_ROOT": data,
                             "CROSS_ALPHABET_SIZES": [2], "CROSS_HORIZON": 3,
                             "BENCHMARK_PAIRS": 2, "BENCHMARK_SEED": 42,
                             "CROSS_RESULTS_ID": "warm-results", "COMPRESS_OUTPUT": True}
                    try:
                        with mock.patch.object(experiments, "_pair_record", legacy_pair_record):
                            importlib.reload(cross_state)
                            with contextlib.redirect_stdout(io.StringIO()):
                                exec(compile(source, str(NOTEBOOK), "exec"), scope)
                        if "cross_preview =" in source:
                            self.assertEqual(len(scope["cross_timings"]), 3)
                            self.assertEqual([r["sample_pairs"] for r in scope["cross_timings"]], [2] * 3)
                        else:
                            self.assertEqual(len(scope["cross_result_dirs"]), 3)
                            for path in scope["cross_result_dirs"]:
                                manifest = json.loads((path / "manifest.json").read_text())
                                self.assertEqual(manifest["pair_count"], 4)
                    finally:
                        importlib.reload(cross_state)


@unittest.skipUnless(HAS_JUPYTER, "notebook execution requires nbformat, nbclient and ipykernel")
class NotebookExecutionTests(unittest.TestCase):
    def test_fresh_kernel_from_root_and_code(self):
        import nbformat
        from nbclient import NotebookClient

        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            batch = write_synthetic_batch(
                data / "alphabet_2" / "states_3" / "smoke",
                [random_dfa(random.Random(i), 3, 2, id=i) for i in range(4)],
                ["0", "1"], run_id="smoke")
            for index, cwd in enumerate((ROOT, ROOT / "code")):
                notebook = nbformat.read(NOTEBOOK, as_version=4)
                nbformat.validate(notebook)
                config = next(cell for cell in notebook.cells
                              if cell.cell_type == "code" and 'RUN_ID = ' in cell.source)
                config.source = (f"RUN_ID = 'smoke'\nALPHABET_SIZES = [2]\nSTATE_COUNTS = [3]\n"
                                 f"CALCULATIONS = 'both'\nHORIZON = 3\nRESULTS_ID = 'smoke-{index}'\n"
                                 f"COMPRESS_OUTPUT = True\nBENCHMARK_PAIRS = 2\nBENCHMARK_SEED = 42\n"
                                 f"DATA_ROOT_OVERRIDE = {str(data)!r}\n")
                for cell in notebook.cells:
                    if cell.cell_type == "code" and "ENABLE_CROSS_STATE =" in cell.source:
                        cell.source = re.sub(r"ENABLE_CROSS_STATE = (?:True|False)",
                                             "ENABLE_CROSS_STATE = False", cell.source)
                NotebookClient(notebook, timeout=90, kernel_name="python3",
                               resources={"metadata": {"path": str(cwd)}}).execute()
                manifest = json.loads((batch / "comparisons" / f"smoke-{index}" / "manifest.json").read_text())
                self.assertEqual(manifest["pair_count"], 6)
                self.assertEqual(manifest["distribution"]["horizon"], 3)
                summary_cell = next(cell for cell in notebook.cells
                                    if cell.cell_type == "code" and cell.source.startswith("summaries ="))
                self.assertTrue(any(output.output_type == "display_data" for output in summary_cell.outputs))

    def test_optional_cross_state_fresh_kernel(self):
        import nbformat
        from nbclient import NotebookClient

        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            for states in (10, 15, 20, 25, 30):
                write_synthetic_batch(
                    data / "alphabet_2" / f"states_{states}" / "cross-smoke",
                    [random_dfa(random.Random(states + i), states, 2, id=i) for i in range(2)],
                    ["0", "1"], run_id="cross-smoke")
            for index, cwd in enumerate((ROOT, ROOT / "code")):
                original = nbformat.read(NOTEBOOK, as_version=4)
                setup = next(cell for cell in original.cells
                             if cell.cell_type == "code" and "import experiments" in cell.source)
                optional_index = next(i for i, cell in enumerate(original.cells)
                                      if cell.cell_type == "markdown" and "## OPTIONAL" in cell.source)
                config = nbformat.v4.new_code_cell(
                    f"RUN_ID = 'cross-smoke'\nALPHABET_SIZES = [2]\nHORIZON = 3\n"
                    f"DATA_ROOT_OVERRIDE = {str(data)!r}\nCOMPRESS_OUTPUT = True\n"
                    "BENCHMARK_PAIRS = 2\nBENCHMARK_SEED = 42\n")
                optional = original.cells[optional_index:]
                optional[1].source = optional[1].source.replace(
                    "ENABLE_CROSS_STATE = False", "ENABLE_CROSS_STATE = True").replace(
                    "CROSS_RESULTS_ID = None", f"CROSS_RESULTS_ID = 'cross-{index}'")
                optional[1].source += ("\nCROSS_RUN_ID = RUN_ID\n"
                                       "CROSS_ALPHABET_SIZES = ALPHABET_SIZES\nCROSS_HORIZON = HORIZON\n")
                notebook = nbformat.v4.new_notebook(cells=[config, setup, *optional])
                NotebookClient(notebook, timeout=90, kernel_name="python3",
                               resources={"metadata": {"path": str(cwd)}}).execute()
                outputs = list((data / "alphabet_2" / "cross_state" / "cross-smoke" /
                                f"cross-{index}").glob("*/manifest.json"))
                self.assertEqual(len(outputs), 3)
                for path in outputs:
                    manifest = json.loads(path.read_text())
                    self.assertEqual(manifest["pair_count"], 4)
                    self.assertTrue(set(manifest["state_counts"]) <= {10, 20, 30})
                self.assertTrue(any(o.output_type == "display_data" for o in notebook.cells[-1].outputs))
