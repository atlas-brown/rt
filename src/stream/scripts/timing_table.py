#!/usr/bin/env python3

import csv
import json
from pathlib import Path

from stream.scripts.summarize_eval import normalize_address


def parse_seconds(value: str) -> float:
    if value.endswith("s"):
        return float(value[:-1])
    return float(value)


def summarize(values: list[float]) -> tuple[float, float, float]:
    if not values:
        return 0.0, 0.0, 0.0
    return (
        sum(values) / len(values),
        min(values),
        max(values),
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    evaluation_results = repo_root / "evaluation_results"

    raw_json_path = evaluation_results / "ann:n_heuristic:y_fst:y" / "evaluation_results.json"
    baseline_csv_path = evaluation_results / "baseline" / "baseline.csv"
    output_path = evaluation_results / "tables" / "timing_table.md"

    raw_results = json.loads(raw_json_path.read_text(encoding="utf-8"))["evaluation_results"]
    baseline_rows = list(csv.DictReader(baseline_csv_path.open(newline="", encoding="utf-8")))

    raw_map = {
        normalize_address((result["address"], result["content"])): result
        for result in raw_results
    }

    rt_times: list[float] = []
    sc_times: list[float] = []
    lt_times: list[float] = []

    for row in baseline_rows:
        key = normalize_address((row["pipeline_file"], row["pipeline"]))
        raw_result = raw_map.get(key)
        if raw_result is None:
            continue
        rt_times.append(parse_seconds(raw_result["evaluation_time"]))
        sc_times.append(float(row["shell check processing time"]))
        lt_times.append(float(row["ltsh processing time"]))

    rows = [
        ("RT (without ann)",) + summarize(rt_times),
        ("ShellCheck",) + summarize(sc_times),
        ("LadderTypes",) + summarize(lt_times),
    ]

    lines = [
        "| System | Mean (s) | Min (s) | Max (s) |",
        "|---|---:|---:|---:|",
    ]
    for system, mean, min_value, max_value in rows:
        lines.append(f"| {system} | {mean:.3f} | {min_value:.3f} | {max_value:.3f} |")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
