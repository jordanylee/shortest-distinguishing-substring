"""Streaming, read-only summaries of one explicitly selected result directory."""

import gzip
import json
from collections import Counter
from pathlib import Path

from similarity_metrics import SCORE_FIELDS


def read_jsonl(path):
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def summarize(result_dir):
    result_dir = Path(result_dir)
    m = json.loads((result_dir / "manifest.json").read_text(encoding="utf-8"))
    if m.get("status") != "complete":
        raise ValueError("only complete results can be summarized")
    hist = Counter()
    groups = {}
    totals = {key: 0.0 for key in SCORE_FIELDS}
    count = equivalent = metric_count = 0
    for row in read_jsonl(result_dir / m["pairs_file"]):
        count += 1
        if "length" in row:
            if row["length"] is None:
                equivalent += 1
            else:
                hist[row["length"]] += 1
        if "probability_of_agreement" in row:
            metric_count += 1
            for key in SCORE_FIELDS:
                totals[key] += row[key]
            group = "equivalent" if row.get("length") is None else str(row["length"])
            if "length" not in row:
                group = "all (SDS not computed)"
            entry = groups.setdefault(group, {"count": 0, **{k: 0.0 for k in SCORE_FIELDS}})
            entry["count"] += 1
            for key in SCORE_FIELDS:
                entry[key] += row[key]
    if count != m["pair_count"]:
        raise ValueError("pair file count does not match manifest")
    for entry in groups.values():
        for key in SCORE_FIELDS:
            entry[key] /= entry["count"]
    finite, positive = sum(hist.values()), sum(n for length, n in hist.items() if length > 0)
    has_sds = m.get("calculations") != "similarity"
    return {"results_id": m["results_id"], "alphabet_size": m["alphabet_size"],
            "state_count": m["state_count"], "distribution": m.get("distribution"),
            "pair_count": count, "equivalent_pair_count": equivalent if has_sds else None,
            "equivalent_rate": equivalent / count if has_sds and count else None,
            "length_histogram": dict(sorted(hist.items())) if has_sds else None,
            "finite_length_distribution": {l: n / finite for l, n in sorted(hist.items())} if finite else {},
            "positive_length_distribution": {l: n / positive for l, n in sorted(hist.items()) if l > 0}
            if positive else {},
            "mean_similarity": {key: totals[key] / metric_count for key in SCORE_FIELDS} if metric_count else None,
            "similarity_by_sds_length": groups, "reachable_histogram": m["reachable_histogram"],
            "minimal_histogram": m["minimal_histogram"]}


def markdown_summary(summary):
    """Notebook-friendly tables, without requiring pandas or plotting packages."""
    s = summary
    lines = [f"### Alphabet {s['alphabet_size']}, states {s['state_count']}", "",
             f"Results: `{s['results_id']}`; pairs: {s['pair_count']:,}.", ""]
    if s["distribution"]:
        lines.extend([f"Similarity horizon: {s['distribution']['horizon']} (uniform length and symbols).", ""])
    if s["equivalent_pair_count"] is not None:
        rate = "n/a" if s["equivalent_rate"] is None else f"{s['equivalent_rate']:.3%}"
        lines.extend([f"Equivalent pairs: {s['equivalent_pair_count']:,} ({rate}).", "",
                      "| SDS length | Count | Fraction of finite lengths | Fraction conditional on L>0 |",
                      "|---|---:|---:|---:|"])
        for length, count in s["length_histogram"].items():
            positive = s["positive_length_distribution"].get(length)
            conditional = "—" if positive is None else f"{positive:.3%}"
            lines.append(f"| {length} | {count:,} | {s['finite_length_distribution'][length]:.3%} | {conditional} |")
        lines.append("")
    if s["mean_similarity"] is not None:
        lines.extend(["| SDS group | Pairs | Mean agreement | Mean weighted Jaccard |",
                      "|---|---:|---:|---:|"])
        means = s["mean_similarity"]
        lines.append(f"| All | {s['pair_count']:,} | {means['probability_of_agreement']:.6f} | {means['weighted_jaccard']:.6f} |")
        for group, entry in s["similarity_by_sds_length"].items():
            lines.append(f"| {group} | {entry['count']:,} | {entry['probability_of_agreement']:.6f} | {entry['weighted_jaccard']:.6f} |")
        lines.append("")
    lines.extend(["| DFA statistic | Size: count |", "|---|---|"])
    for name in ("reachable", "minimal"):
        counts = s[name + "_histogram"]
        formatted = ", ".join(f"{size}: {count}" for size, count in sorted(counts.items(), key=lambda item: int(item[0])))
        lines.append(f"| {name.capitalize()} | {formatted} |")
    return "\n".join(lines)
