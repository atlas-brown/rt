import csv
import json

from stream.evaluation_summary import raw_json_to_bug_detection, results_to_overview_csv


def _write_json(path, records):
    path.write_text(json.dumps({"evaluation_results": records}), encoding="utf-8")


def _record(address, content, is_buggy, warning_signaled):
    return {
        "address": address,
        "content": content,
        "is buggy?": is_buggy,
        "warning signaled?": warning_signaled,
        "evaluation_time": 0.1,
        "tool runtime error": None,
        "category": None,
        "notes": "",
    }


def test_overview_and_bug_detection_skip_records_missing_baseline(tmp_path):
    ann_json = tmp_path / "ann.json"
    raw_json = tmp_path / "raw.json"
    baseline_csv = tmp_path / "baseline.csv"
    overview_csv = tmp_path / "overview.csv"
    bug_detection_csv = tmp_path / "bug_detection.csv"

    shared_with_baseline = "./full_benchmark/handwritten/valid/3.sh"
    shared_without_baseline = "./full_benchmark/handwritten/valid/4.sh"
    pipeline_a = "echo a | wc -l"
    pipeline_b = "echo b | wc -l"

    _write_json(
        ann_json,
        [
            _record(shared_with_baseline, pipeline_a, False, False),
            _record(shared_without_baseline, pipeline_b, True, True),
        ],
    )
    _write_json(
        raw_json,
        [
            _record(shared_with_baseline, pipeline_a, False, False),
            _record(shared_without_baseline, pipeline_b, True, False),
        ],
    )

    with baseline_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "pipeline_file",
                "pipeline",
                "is buggy?",
                "shell check warning?",
                "ltsh warning?",
                "shell check processing time",
                "ltsh processing time",
                "shell check links",
            ]
        )
        writer.writerow(
            [
                shared_with_baseline,
                pipeline_a,
                "false",
                "false",
                "false",
                "0.0",
                "0.0",
                "",
            ]
        )

    results_to_overview_csv(
        str(ann_json),
        str(raw_json),
        str(baseline_csv),
        str(overview_csv),
    )
    raw_json_to_bug_detection(
        str(raw_json),
        str(baseline_csv),
        str(bug_detection_csv),
    )

    with overview_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    handwritten_rows = [row for row in rows if row["Benchmark set"] == "Handwritten"]
    unique_rows = {
        (row["With Annotations?"], row["SC Accuracy"], row["LT Accuracy"])
        for row in handwritten_rows
    }
    assert unique_rows == {
        ("True", "1.0", "1.0"),
        ("False", "1.0", "1.0"),
    }

    with bug_detection_csv.open("r", encoding="utf-8", newline="") as handle:
        bug_rows = list(csv.DictReader(handle))
    assert len(bug_rows) == 3
    assert all(row["Only this detects"] == "0" for row in bug_rows)
