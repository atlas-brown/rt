import json

import pytest

from stream import run_evaluations
from stream.type_checker import CheckingResult


def test_run_all_evaluations_writes_runtime_error_report(monkeypatch, tmp_path):
    valid_dir = tmp_path / "valid"
    valid_dir.mkdir()
    script_path = valid_dir / "broken.sh"
    script_path.write_text("echo broken\n", encoding="utf-8")

    output_dir = tmp_path / "results"
    output_json = output_dir / "evaluation_results.json"
    summary_csv = output_dir / "summary.csv"
    parsing_error_log = tmp_path / "parsing_errors.log"

    monkeypatch.setitem(
        run_evaluations.CONFIG._config,
        "parsing_error_log_path",
        str(parsing_error_log),
    )

    class ExplodingChecker:
        def __init__(self, *args, **kwargs):
            self.pipeline = "printf 'broken\\n' | sort"

        def check_next(self):
            raise RuntimeError("synthetic crash for test")

        def get_current_pipeline_content_when_error(self):
            return self.pipeline

    monkeypatch.setattr(run_evaluations, "ScriptChecker", ExplodingChecker)

    run_evaluations.run_all_evaluations(
        valid_dirs=[str(valid_dir)],
        invalid_dirs=[],
        output_json=str(output_json),
        output_summary_csv=str(summary_csv),
        not_check_all_dirs=[],
        num_workers=1,
    )

    runtime_error_log = output_dir / "runtime_errors.log"
    assert runtime_error_log.exists()

    log_text = runtime_error_log.read_text(encoding="utf-8")
    assert "Runtime error #1" in log_text
    assert f"Address: {script_path}" in log_text
    assert "Pipeline: printf 'broken\\n' | sort" in log_text
    assert "Exception type: RuntimeError" in log_text
    assert "Error: synthetic crash for test" in log_text
    assert "Traceback:" in log_text
    assert "raise RuntimeError(\"synthetic crash for test\")" in log_text

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["evaluation_results"][0]["tool runtime error"] == "synthetic crash for test"


@pytest.mark.parametrize(
    ("runtime_kind", "runtime_message", "exception_type", "json_field", "traceback_field"),
    [
        ("tool runtime error", "inner synthetic crash", "RuntimeError", "tool runtime error", "tool runtime traceback"),
        ("pash annotations error", "inner synthetic annotation crash", "PashAnnotationParsingError", "pash annotations error", "pash annotations traceback"),
    ],
)
def test_run_all_evaluations_writes_pipeline_runtime_details(
    monkeypatch,
    tmp_path,
    runtime_kind,
    runtime_message,
    exception_type,
    json_field,
    traceback_field,
):
    valid_dir = tmp_path / "valid"
    valid_dir.mkdir()
    script_path = valid_dir / "broken.sh"
    script_path.write_text("echo broken\n", encoding="utf-8")

    output_dir = tmp_path / "results"
    output_json = output_dir / "evaluation_results.json"
    summary_csv = output_dir / "summary.csv"
    parsing_error_log = tmp_path / "parsing_errors.log"

    monkeypatch.setitem(
        run_evaluations.CONFIG._config,
        "parsing_error_log_path",
        str(parsing_error_log),
    )

    class CheckerWithInnerRuntimeError:
        def __init__(self, *args, **kwargs):
            self.done = False

        def check_next(self):
            if self.done:
                return None
            self.done = True
            return CheckingResult(
                error_results=[],
                self_contained=True,
                pipeline_content="printf 'broken\\n' | sort",
                pipeline_length=2,
                max_automata_size=7,
                runtime_error_kind=runtime_kind,
                runtime_error_message=runtime_message,
                runtime_error_type=exception_type,
                runtime_error_traceback=(
                    "Traceback (most recent call last):\n"
                    f"{exception_type}: {runtime_message}\n"
                ),
            )

    monkeypatch.setattr(run_evaluations, "ScriptChecker", CheckerWithInnerRuntimeError)

    run_evaluations.run_all_evaluations(
        valid_dirs=[str(valid_dir)],
        invalid_dirs=[],
        output_json=str(output_json),
        output_summary_csv=str(summary_csv),
        not_check_all_dirs=[],
        num_workers=1,
    )

    runtime_error_log = output_dir / "runtime_errors.log"
    log_text = runtime_error_log.read_text(encoding="utf-8")
    assert "Runtime error #1" in log_text
    assert f"Address: {script_path}" in log_text
    assert "Pipeline: printf 'broken\\n' | sort" in log_text
    assert f"Error kind: {runtime_kind}" in log_text
    assert f"Exception type: {exception_type}" in log_text
    assert f"Error: {runtime_message}" in log_text

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    result = payload["evaluation_results"][0]
    assert result[json_field] == runtime_message
    assert exception_type in result[traceback_field]
    assert result["warning signaled?"] is None
