#!/usr/bin/env python3

import csv
from pathlib import Path


def load_summary_counts(path: Path) -> tuple[int, int, int, int]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    correct = next(row for row in rows if row and row[0] == "correct")
    buggy = next(row for row in rows if row and row[0] == "buggy")

    correct_total = int(correct[1])
    false_positives = int(correct[4])
    buggy_total = int(buggy[1])
    buggy_right = int(buggy[3])

    correct_right = correct_total - false_positives
    return correct_right, correct_total, buggy_right, buggy_total


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    evaluation_results = repo_root / "evaluation_results"

    summaries = {
        ("w/o ann", "RT"): evaluation_results / "ann:n_heuristic:y_fst:y/summary.csv",
        ("w/o ann", "w/o heus"): evaluation_results / "ann:n_heuristic:n_fst:y/summary.csv",
        ("w/o ann", "w/o FSTs"): evaluation_results / "ann:n_heuristic:y_fst:n/summary.csv",
        ("w/o ann", "w/o con"): evaluation_results / "ann:n_heuristic:y_fst:y_concretization:n/summary.csv",
        ("w/ ann", "RT"): evaluation_results / "ann:y_heuristic:y_fst:y/summary.csv",
        ("w/ ann", "w/o heus"): evaluation_results / "ann:y_heuristic:n_fst:y/summary.csv",
        ("w/ ann", "w/o FSTs"): evaluation_results / "ann:y_heuristic:y_fst:n/summary.csv",
        ("w/ ann", "w/o con"): evaluation_results / "ann:y_heuristic:y_fst:y_concretization:n/summary.csv",
    }

    table = {}
    for key, path in summaries.items():
        table[key] = load_summary_counts(path)

    output_path = evaluation_results / "tables" / "ablation_table.md"
    lines = [
        "| Ann | Label | RT | w/o heus | w/o FSTs | w/o con |",
        "|---|---|---:|---:|---:|---:|",
    ]

    for ann_label in ("w/o ann", "w/ ann"):
        correct_rt, correct_total, buggy_rt, buggy_total = table[(ann_label, "RT")]
        correct_wo_heus, _, buggy_wo_heus, _ = table[(ann_label, "w/o heus")]
        correct_wo_fsts, _, buggy_wo_fsts, _ = table[(ann_label, "w/o FSTs")]
        correct_wo_con, _, buggy_wo_con, _ = table[(ann_label, "w/o con")]

        lines.append(
            f"| {ann_label} | correct | {correct_rt} / {correct_total} | {correct_wo_heus} / {correct_total} | {correct_wo_fsts} / {correct_total} | {correct_wo_con} / {correct_total} |"
        )
        lines.append(
            f"| {ann_label} | buggy | {buggy_rt} / {buggy_total} | {buggy_wo_heus} / {buggy_total} | {buggy_wo_fsts} / {buggy_total} | {buggy_wo_con} / {buggy_total} |"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
