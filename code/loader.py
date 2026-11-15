"""Load one generated DFA batch (see data/DFA_Generator.py, schema_version 1).

This is the only module that knows the on-disk format. Other modules, including
the planned similarity metrics, should call `load_batch` instead of parsing files.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

SUPPORTED_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class DFA:
    id: int
    delta: tuple[tuple[int, ...], ...]  # delta[state][symbol_index] -> state
    accept: tuple[bool, ...]            # accept[state]
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


class BatchFormatError(ValueError):
    """The run directory, manifest or a record does not match the expected format."""


class AlphabetMismatchError(ValueError):
    """A transition row's width does not match the alphabet size."""


def _fail(exc_type: type[Exception], run_dir: Path, message: str, record_id=None) -> None:
    where = f"{run_dir}" if record_id is None else f"{run_dir} record id={record_id}"
    full = f"{where}: {message}"
    log.error(full)
    raise exc_type(full)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _open_text(path: Path):
    # Compression is detected from the file name; older manifests lack a `compression` field.
    if path.name.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")


def load_batch(run_dir: Path) -> Batch:
    run_dir = Path(run_dir)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        _fail(BatchFormatError, run_dir, "manifest.json not found")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # ---- Format mapping: manifest fields (schema_version 1) ---------------------------
    try:
        schema_version = manifest.get("schema_version")
        status = manifest.get("status")
        if status != "complete":
            _fail(BatchFormatError, run_dir, f"manifest status is {status!r}, expected 'complete'")
        if schema_version != SUPPORTED_SCHEMA_VERSION:
            _fail(BatchFormatError, run_dir, f"unsupported schema_version {schema_version!r}")
        run_id = manifest["run_id"]
        n_states = manifest["state_count"]
        alphabet_size = manifest["alphabet_size"]
        alphabet = tuple(manifest["alphabet"])
        sample_count = manifest["sample_count"]
        batch_file = manifest["batch_file"]
    except KeyError as e:
        _fail(BatchFormatError, run_dir, f"manifest missing field {e.args[0]!r}")
    # -----------------------------------------------------------------------------------

    if type(n_states) is not int or n_states < 1:
        _fail(BatchFormatError, run_dir, f"invalid state_count {n_states!r}")
    if not all(isinstance(s, str) for s in alphabet) or len(set(alphabet)) != len(alphabet):
        _fail(BatchFormatError, run_dir, f"invalid alphabet {list(alphabet)!r}")
    if len(alphabet) != alphabet_size:
        _fail(AlphabetMismatchError, run_dir,
              f"alphabet has {len(alphabet)} symbols but alphabet_size is {alphabet_size}")
    if Path(batch_file).name != batch_file:
        _fail(BatchFormatError, run_dir, f"batch_file must be a bare file name, got {batch_file!r}")
    batch_path = run_dir / batch_file
    if not batch_path.is_file():
        _fail(BatchFormatError, run_dir, f"batch file {batch_file!r} not found")

    n_symbols = len(alphabet)
    dfas: list[DFA] = []
    seen_ids: set[int] = set()
    with _open_text(batch_path) as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                _fail(BatchFormatError, run_dir, f"line {line_no}: invalid JSON ({e})")
            if not isinstance(rec, dict):
                _fail(BatchFormatError, run_dir, f"line {line_no}: record is not a JSON object")

            # ---- Format mapping: one record -> DFA ------------------------------------
            rid = rec.get("id")
            if type(rid) is not int:
                _fail(BatchFormatError, run_dir, f"line {line_no}: id must be an int", rid)
            if rid in seen_ids:
                _fail(BatchFormatError, run_dir, "duplicate record id", rid)
            seen_ids.add(rid)
            try:
                table = rec["transitions"]
                acceptance = rec["acceptance"]
                initial = rec["initial_state"]
            except KeyError as e:
                _fail(BatchFormatError, run_dir, f"record missing field {e.args[0]!r}", rid)
            # ---------------------------------------------------------------------------

            if not isinstance(table, list) or not isinstance(acceptance, list):
                _fail(BatchFormatError, run_dir, "transitions and acceptance must be lists", rid)
            if len(table) != n_states or len(acceptance) != n_states:
                _fail(BatchFormatError, run_dir,
                      f"expected {n_states} states, got {len(table)} transition rows "
                      f"and {len(acceptance)} acceptance flags", rid)
            if type(initial) is not int or not 0 <= initial < n_states:
                _fail(BatchFormatError, run_dir, f"initial_state {initial!r} out of range", rid)
            if any(type(flag) is not bool for flag in acceptance):
                _fail(BatchFormatError, run_dir, "acceptance flags must be booleans", rid)
            for state, row in enumerate(table):
                if not isinstance(row, list) or len(row) != n_symbols:
                    width = len(row) if isinstance(row, list) else type(row).__name__
                    _fail(AlphabetMismatchError, run_dir,
                          f"state {state} transition row has width {width}, "
                          f"alphabet has {n_symbols} symbols", rid)
                if any(type(dst) is not int or not 0 <= dst < n_states for dst in row):
                    _fail(BatchFormatError, run_dir,
                          f"state {state} has an invalid destination in {row!r}", rid)

            dfas.append(DFA(id=rid,
                            delta=tuple(tuple(row) for row in table),
                            accept=tuple(acceptance),
                            initial=initial))

    if len(dfas) != sample_count:
        _fail(BatchFormatError, run_dir,
              f"found {len(dfas)} records but sample_count is {sample_count}")

    return Batch(
        run_dir=run_dir,
        run_id=run_id,
        alphabet=alphabet,
        n_states=n_states,
        dfas=tuple(dfas),
        manifest=manifest,
        input_sha256={"manifest.json": _sha256(manifest_path), batch_file: _sha256(batch_path)},
    )
