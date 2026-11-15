# %%
# Change these parameters, then run all cells. Requires Python 3.10+.
from pathlib import Path

DFAS_PER_COMBINATION = 500
STATE_COUNTS = [10, 20, 30]  # Starting defaults; edit for your experiment.
ALPHABET_SIZES = [2, 3]     # Starting defaults; symbols are "0", "1", ...
MASTER_SEED = 42
RUN_ID = None  # None uses a readable UTC date/time; or choose a descriptive run name.
REPOSITORY_ROOT = None  # Auto-detect from cwd; otherwise set Path(r"...").
VERIFY_SAVED_BATCHES = True  # Reload and reproduce every saved DFA.
COMPRESS_OUTPUT = False  # True: .jsonl.gz; False: plain .jsonl.

# %% [markdown]
# # DFA Generator
# Run all cells in `DFA_Generator.ipynb`, or run this companion Python file.
# The first cell controls the run. Defaults produce 3,000 DFAs: 500 for each
# of six combinations. No training libraries are needed for generation.
#
# Output: `data/alphabet_<A>/states_<S>/<run_id>/` with `manifest.json`
# and `dfas_alphabet-<A>_states-<S>_count-<N>_<UTC-date-time>.jsonl`.
# Set COMPRESS_OUTPUT=True to add `.gz`. Default run folders use readable
# UTC timestamps, e.g. `2026-11-15_00-38-53-123456_UTC`. Microseconds avoid
# collisions between quick reruns. Each batch filename includes its generation
# timestamp even when RUN_ID is customized. Individual record IDs remain
# zero-based indices within their batch; their seeds enable exact replay.
# Each line is one DFA. Rows of `transitions` are states;
# columns follow the manifest's `alphabet`. State 0 is initial, and
# `acceptance[state]` indicates whether a state accepts. Strings of symbols
# must be treated as sequences of tokens, especially for alphabets above 10.
#
# These are raw DeepDFA samples: not necessarily reachable, minimal, distinct,
# or language-inequivalent. DeepDFA forces a forward edge from each state
# except the last, so this is not uniform sampling over all complete DFAs.
#
# Seeds depend on (master seed, alphabet size, state count, sample index),
# independent of the order of parameter lists. Python version and generator
# source hash are recorded because exact replay also depends on these.
# Existing run directories are never overwritten. On failure, a directory may
# contain a partial batch; only runs with a completed manifest are complete.

# %%
import gzip
import hashlib
import importlib.util
import json
import platform
import random
import re
import subprocess
from datetime import datetime, timezone


def find_repository_root(explicit=None):
    candidates = [Path(explicit)] if explicit is not None else [Path.cwd(), *Path.cwd().parents]
    if explicit is None and "__file__" in globals():
        candidates.append(Path(__file__).resolve().parents[1])
    for candidate in candidates:
        root = candidate.resolve()
        if (root / "DeepDFA" / "Random_DFA.py").is_file():
            return root
    raise FileNotFoundError("Cannot find DeepDFA/Random_DFA.py. Set REPOSITORY_ROOT to the repository root.")


def positive_integer(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer.")


def validate_record(record, states, symbols):
    if record["initial_state"] != 0:
        raise ValueError("Initial state must be 0.")
    table, acceptance = record["transitions"], record["acceptance"]
    if len(table) != states or len(acceptance) != states:
        raise ValueError("State count does not match the stored data.")
    if any(type(flag) is not bool for flag in acceptance):
        raise ValueError("Acceptance flags must be booleans.")
    for row in table:
        if len(row) != symbols or any(type(dst) is not int or not 0 <= dst < states for dst in row):
            raise ValueError("Invalid or incomplete transition table.")


def sample_record(generator, master_seed, states, symbols, index):
    seed_input = json.dumps([master_seed, symbols, states, index], separators=(",", ":"))
    seed = int.from_bytes(hashlib.sha256(seed_input.encode("utf-8")).digest(), "big")
    # Upstream uses global random; preserve the notebook user's RNG state.
    previous_state = random.getstate()
    try:
        random.seed(seed)
        dfa = generator(states, symbols)
    finally:
        random.setstate(previous_state)
    alphabet = [str(a) for a in range(symbols)]
    if set(dfa.transitions) != set(range(states)) or any(
        set(dfa.transitions[s]) != set(alphabet) for s in range(states)
    ):
        raise ValueError("Generator returned unexpected states or symbols.")
    record = {
        "id": index,
        "seed": str(seed),  # Decimal string avoids integer precision loss in other tools.
        "initial_state": 0,
        "transitions": [[dfa.transitions[s][a] for a in alphabet] for s in range(states)],
        "acceptance": list(dfa.acceptance),
    }
    validate_record(record, states, symbols)
    return record


def open_batch(path, mode="rt"):
    """Open plain or gzip JSON Lines, including temporary batch files."""
    opener = gzip.open if Path(path).name.endswith((".gz", ".gz.part")) else open
    return opener(path, mode, encoding="utf-8", newline="\n")


def verify_batch(path, generator, master_seed, states, symbols, count):
    actual_count = 0
    with open_batch(path) as stream:
        for index, line in enumerate(stream):
            record = json.loads(line)
            validate_record(record, states, symbols)
            if record != sample_record(generator, master_seed, states, symbols, index):
                raise ValueError(f"Saved DFA {index} did not reproduce exactly.")
            actual_count += 1
    if actual_count != count:
        raise ValueError(f"Expected {count} records, found {actual_count}.")
    return actual_count


def generate_batches(root, count, state_counts, alphabet_sizes, master_seed, run_id=None, verify=True, compress=False):
    positive_integer(count, "DFAS_PER_COMBINATION")
    if type(compress) is not bool:
        raise ValueError("COMPRESS_OUTPUT must be True or False.")
    if type(master_seed) is not int:
        raise ValueError("MASTER_SEED must be an integer.")
    for values, name in [(state_counts, "STATE_COUNTS"), (alphabet_sizes, "ALPHABET_SIZES")]:
        if not isinstance(values, (list, tuple)) or not values:
            raise ValueError(f"{name} must be a nonempty list or tuple.")
        for value in values:
            positive_integer(value, name)
        if len(set(values)) != len(values):
            raise ValueError(f"{name} must not contain duplicates.")
    root = find_repository_root(root)
    run_started = datetime.now(timezone.utc)
    timestamp = run_started.strftime("%Y-%m-%d_%H-%M-%S-%f_UTC")
    run_id = run_id if run_id is not None else timestamp
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", run_id):
        raise ValueError("RUN_ID must be 1-100 letters, digits, underscores or hyphens, starting with a letter or digit.")
    targets = [(s, a, root / "data" / f"alphabet_{a}" / f"states_{s}" / run_id)
               for a in alphabet_sizes for s in state_counts]
    for _, _, directory in targets:
        if directory.exists():
            raise FileExistsError(f"Run directory already exists: {directory}. Choose a new RUN_ID.")

    source = root / "DeepDFA" / "Random_DFA.py"
    spec = importlib.util.spec_from_file_location("deepdfa_generation_source", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        commit = subprocess.run(["git", "-C", str(source.parent), "rev-parse", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    provenance = {"deepdfa_commit": commit, "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                  "python_version": platform.python_version(), "python_implementation": platform.python_implementation()}
    print(f"Run {run_id}: {len(targets)} combinations, {count * len(targets):,} DFAs")
    summaries = []
    for states, symbols, directory in targets:
        directory.mkdir(parents=True, exist_ok=False)
        batch_name = f"dfas_alphabet-{symbols}_states-{states}_count-{count}_{timestamp}.jsonl"
        if compress:
            batch_name += ".gz"
        partial = directory / (batch_name + ".part")
        with open_batch(partial, "wt") as stream:
            for index in range(count):
                record = sample_record(module.Random_DFA, master_seed, states, symbols, index)
                stream.write(json.dumps(record, separators=(",", ":")) + "\n")
        if verify:
            verify_batch(partial, module.Random_DFA, master_seed, states, symbols, count)
        batch = directory / batch_name
        partial.rename(batch)
        manifest = {
            "schema_version": 1, "status": "complete", "run_id": run_id,
            "run_started_utc": run_started.isoformat(),
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "state_count": states, "alphabet_size": symbols,
            "alphabet": [str(a) for a in range(symbols)], "sample_count": count,
            "master_seed": str(master_seed),
            "seed_scheme": "SHA256 of UTF-8 compact JSON [master_seed, alphabet_size, state_count, zero_based_index], interpreted as unsigned big-endian integer",
            "record_seed_encoding": "decimal string", "initial_state": 0,
            "transition_layout": "transitions[state][alphabet_column] = destination_state",
            "acceptance_layout": "acceptance[state] = boolean",
            "generator": "DeepDFA/Random_DFA.py:Random_DFA",
            "sampling": "raw upstream samples; forward-edge bias; no filtering or minimization",
            "batch_file": batch.name, "compression": "gzip" if compress else "none",
            "batch_bytes": batch.stat().st_size,
            "compressed_bytes": batch.stat().st_size if compress else None,
            "saved_records_verified": verify, **provenance,
        }
        manifest_partial = directory / "manifest.json.part"
        manifest_partial.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        manifest_partial.rename(directory / "manifest.json")
        summaries.append({"alphabet_size": symbols, "state_count": states, "count": count, "path": str(batch)})
        print(f"  A={symbols}, S={states}: {count} saved ({batch.stat().st_size:,} bytes) -> {batch}")
    return summaries

# %%
if __name__ == "__main__":
    generated_batches = generate_batches(
        REPOSITORY_ROOT, DFAS_PER_COMBINATION, STATE_COUNTS, ALPHABET_SIZES,
        MASTER_SEED, RUN_ID, VERIFY_SAVED_BATCHES, COMPRESS_OUTPUT,
    )

# %% [markdown]
# ## Reload a batch
# Run the next cell after generation. It streams the batch rather than loading
# all DFAs at once. Use the manifest's alphabet order when following transitions.
# Reconstruct an upstream object only if needed; JSON contains the full DFA.

# %%
if __name__ == "__main__":
    first_batch = Path(generated_batches[0]["path"])
    first_manifest = json.loads((first_batch.parent / "manifest.json").read_text(encoding="utf-8"))
    with open_batch(first_batch) as stream:
        first_dfa = json.loads(next(stream))
    print("First batch alphabet:", first_manifest["alphabet"])
    print("First DFA ID:", first_dfa["id"], "| states:", len(first_dfa["transitions"]))
