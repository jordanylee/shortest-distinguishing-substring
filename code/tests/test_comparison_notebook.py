"""Execute the real notebook on temporary data; never write to project data/."""

import importlib.util
import json
import random
import re
import tempfile
import unittest
from pathlib import Path

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
                NotebookClient(notebook, timeout=90, kernel_name="python3",
                               resources={"metadata": {"path": str(cwd)}}).execute()
                manifest = json.loads((batch / "comparisons" / f"smoke-{index}" / "manifest.json").read_text())
                self.assertEqual(manifest["pair_count"], 6)
                self.assertEqual(manifest["distribution"]["horizon"], 3)
                summary_cell = notebook.cells[-1]
                self.assertTrue(any(output.output_type == "display_data" for output in summary_cell.outputs))
