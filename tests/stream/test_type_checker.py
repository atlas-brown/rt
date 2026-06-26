import pytest

from stream.parser.shell_parser import ShellParser
from stream.regular_type import RegularType
from stream.type_checker import ErrorResult, PipelineChecker, ScriptChecker


def test_input_compatibility_produces_error_result(tmp_path):
    script = tmp_path / "test.sh"
    script.write_text("echo abc | sort -n\n", encoding="utf-8")

    checker = ScriptChecker(str(script))
    result = checker.check_next()
    assert result is not None

    sort_errors = [err for err in result.error_results if err.command_name == "sort"]
    assert len(sort_errors) == 1

    error = sort_errors[0]
    assert isinstance(error, ErrorResult)
    assert error.serious_violation is True
    assert error.witness is not None
    assert len(error.witness) > 0


def test_empty_output_rule_triggers_error_result(tmp_path):
    script = tmp_path / "test.sh"
    script.write_text("echo hello | grep zzz\n", encoding="utf-8")

    checker = ScriptChecker(str(script), enable_rule_no_empty_output=True)
    result = checker.check_next()
    assert result is not None

    grep_errors = [err for err in result.error_results if err.command_name == "grep"]
    assert len(grep_errors) == 1

    error = grep_errors[0]
    assert error.serious_violation is False
    assert error.all_input is True


def test_violated_assertion_produces_error_result(tmp_path):
    script = tmp_path / "test.sh"
    script.write_text('# @assert "echo hello" --> "xyz"\necho hello | tr a-z A-Z\n', encoding="utf-8")

    checker = ScriptChecker(str(script))
    result = checker.check_next()
    assert result is not None

    echo_errors = [err for err in result.error_results if err.command_name == "echo"]
    assert len(echo_errors) == 1

    error = echo_errors[0]
    assert error.serious_violation is True
    assert error.witness is not None


def test_correct_assertion_produces_no_error(tmp_path):
    script = tmp_path / "test.sh"
    script.write_text('# @assert "echo hello" --> "hello"\necho hello | tr a-z A-Z\n', encoding="utf-8")

    checker = ScriptChecker(str(script))
    result = checker.check_next()
    assert result is not None

    echo_errors = [err for err in result.error_results if err.command_name == "echo"]
    assert len(echo_errors) == 0


def test_backward_tracing_returns_expected_witness_and_index():
    checker = PipelineChecker({}, {}, [])
    checker.backward_map[0] = lambda nfa: RegularType("abc").nfa
    checker.backward_map[1] = lambda nfa: RegularType("def").nfa

    witness, index = checker.backward("xyz", 3)
    assert witness == "abc"
    assert index == 0


def test_statistics_are_populated_after_checking(tmp_path):
    script = tmp_path / "test.sh"
    script.write_text("echo hello | tr a-z A-Z\n", encoding="utf-8")

    checker = ScriptChecker(str(script))
    result = checker.check_next()
    assert result is not None
    assert result.pipeline_length > 0
    assert result.max_automata_size >= 1
    assert result.statistics_time >= 0


def test_script_checker_iteration_exhaustion(tmp_path):
    script = tmp_path / "test.sh"
    script.write_text("echo hello | tr a-z A-Z\n", encoding="utf-8")

    checker = ScriptChecker(str(script))
    result1 = checker.check_next()
    assert result1 is not None
    result2 = checker.check_next()
    assert result2 is None
