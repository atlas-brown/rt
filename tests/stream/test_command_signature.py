import pytest
from pash_annotations.datatypes.BasicDatatypes import Flag, Operand, Option
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from stream.command_signature import CommandSignature, InferenceResult
from stream.regular_type import RegularType
from stream.transformation_ast import ConstantTransform
from stream.user_annotation import AnnotationType, EnvAnnotation

# ---------------------------------------------------------------------------
# get_input_type
# ---------------------------------------------------------------------------


def test_get_input_type_updates_based_on_flags(lookup_signature):
    sort_sig = lookup_signature("sort")

    # Default (no flags)
    inv = CommandInvocationInitial("sort", [], [])
    input_type, no_input_type = sort_sig.get_input_type(inv, [], {})
    assert input_type.pattern == ".*"

    # With -n flag
    inv = CommandInvocationInitial("sort", [Flag("-n")], [])
    input_type, no_input_type = sort_sig.get_input_type(inv, [], {})
    assert input_type.pattern == "[[:blank:]]*[-+]?[0-9]+.*"

    # With -h flag
    inv = CommandInvocationInitial("sort", [Flag("-h")], [])
    input_type, no_input_type = sort_sig.get_input_type(inv, [], {})
    assert input_type.pattern == "[[:blank:]]*[-+]?[0-9]+.*"


def test_get_input_type_for_grep(lookup_signature):
    grep_sig = lookup_signature("grep")
    inv = CommandInvocationInitial(
        "grep", [], [Operand("pattern"), Operand("file.txt")]
    )
    input_type, no_input_type = grep_sig.get_input_type(inv, [], {})
    assert input_type.pattern == ".*"
    assert no_input_type is None


# ---------------------------------------------------------------------------
# _matches_invocation_constraints
# ---------------------------------------------------------------------------


def test_matches_invocation_constraints_with_exact_flag_options_and_operands():
    sig = CommandSignature(
        "test",
        ".*",
        ".*",
        [],
        [],
        [],
        True,
        True,
        match={
            "flag_options": [{"name": "-n"}],
            "operands": ["file.txt"],
        },
    )

    matching_inv = CommandInvocationInitial("test", [Flag("-n")], [Operand("file.txt")])
    assert sig._matches_invocation_constraints(matching_inv) is True

    non_matching_flag = CommandInvocationInitial(
        "test", [Flag("-v")], [Operand("file.txt")]
    )
    assert sig._matches_invocation_constraints(non_matching_flag) is False

    non_matching_operand = CommandInvocationInitial(
        "test", [Flag("-n")], [Operand("other.txt")]
    )
    assert sig._matches_invocation_constraints(non_matching_operand) is False


def test_matches_invocation_constraints_without_match():
    sig = CommandSignature("test", ".*", ".*", [], [], [], True, True, match={})
    inv = CommandInvocationInitial("test", [Flag("-x")], [Operand("anything")])
    assert sig._matches_invocation_constraints(inv) is True


# ---------------------------------------------------------------------------
# match_specificity
# ---------------------------------------------------------------------------


def test_match_specificity_increases_with_more_specific_fields():
    sig_empty = CommandSignature("test", ".*", ".*", [], [], [], True, True, match={})
    sig_flags = CommandSignature(
        "test", ".*", ".*", [], [], [], True, True, match={"flags": ["-n"]}
    )
    sig_flag_options = CommandSignature(
        "test",
        ".*",
        ".*",
        [],
        [],
        [],
        True,
        True,
        match={"flag_options": [{"name": "-n"}], "operands": ["file.txt"]},
    )

    assert sig_empty.match_specificity() == 0
    assert sig_flags.match_specificity() == 2  # 1 + len(flags)
    assert (
        sig_flag_options.match_specificity() == 3
    )  # 1 + len(flag_options) + len(operands)


# ---------------------------------------------------------------------------
# _get_xargs_command
# ---------------------------------------------------------------------------


def test_get_xargs_command_with_various_operands():
    assert (
        CommandSignature._get_xargs_command(
            CommandInvocationInitial("xargs", [], [Operand("-0"), Operand("ls")])
        )
        == "ls"
    )

    assert (
        CommandSignature._get_xargs_command(
            CommandInvocationInitial("xargs", [], [Operand("--"), Operand("echo")])
        )
        == "echo"
    )

    assert (
        CommandSignature._get_xargs_command(
            CommandInvocationInitial(
                "xargs", [], [Operand("-n"), Operand("3"), Operand("cat")]
            )
        )
        == "cat"
    )

    assert (
        CommandSignature._get_xargs_command(
            CommandInvocationInitial(
                "xargs",
                [],
                [Operand("-I"), Operand("{}"), Operand("echo"), Operand("{}")],
            )
        )
        == "echo"
    )

    assert (
        CommandSignature._get_xargs_command(
            CommandInvocationInitial("xargs", [], [Operand("echo"), Operand("hello")])
        )
        == "echo"
    )


# ---------------------------------------------------------------------------
# _xargs_uses_explicit_delimiter
# ---------------------------------------------------------------------------


def test_xargs_uses_explicit_delimiter():
    assert (
        CommandSignature._xargs_uses_explicit_delimiter(
            CommandInvocationInitial("xargs", [], [Operand("-0")])
        )
        is True
    )

    assert (
        CommandSignature._xargs_uses_explicit_delimiter(
            CommandInvocationInitial("xargs", [], [Operand("--null")])
        )
        is True
    )

    assert (
        CommandSignature._xargs_uses_explicit_delimiter(
            CommandInvocationInitial("xargs", [Option("-d", "\n")], [])
        )
        is True
    )

    assert (
        CommandSignature._xargs_uses_explicit_delimiter(
            CommandInvocationInitial("xargs", [], [Operand("echo")])
        )
        is False
    )


# ---------------------------------------------------------------------------
# construct_output_transform with env annotations
# ---------------------------------------------------------------------------


def test_construct_output_transform_with_file_annotation(lookup_signature):
    cat_sig = lookup_signature("cat")

    env_annotations = {
        "file.txt": [EnvAnnotation(AnnotationType.FILE, "file.txt", "hello", None, "")],
    }
    inv = CommandInvocationInitial("cat", [], [Operand("file.txt")])
    transform, self_contained, tainted = cat_sig.construct_output_transform(
        inv, env_annotations
    )

    assert isinstance(transform, ConstantTransform)
    assert transform.output_type.pattern == "hello"
    assert self_contained is True
    assert tainted is False


def test_construct_output_transform_with_var_annotation(lookup_signature):
    grep_sig = lookup_signature("grep")

    env_annotations = {
        "${PATTERN}": [
            EnvAnnotation(AnnotationType.VAR, "${PATTERN}", "[a-z]+", None, "")
        ],
    }
    inv = CommandInvocationInitial(
        "grep", [], [Operand("${PATTERN}"), Operand("file.txt")]
    )
    transform, self_contained, tainted = grep_sig.construct_output_transform(
        inv, env_annotations
    )

    # The transform should be a ConstantTransform because the env sets the pattern
    assert isinstance(transform, ConstantTransform)
    # grep signature is self_contained=False when reading from file without annotations
    assert self_contained is False
    assert tainted is True


# ---------------------------------------------------------------------------
# apply_command_type integration
# ---------------------------------------------------------------------------


def test_apply_command_type_integration_for_cat_grep_sort(lookup_signature):
    cat_sig = lookup_signature("cat")
    grep_sig = lookup_signature("grep")
    sort_sig = lookup_signature("sort")

    # cat with file operand (no env annotations -> falls back to .*)
    inv = CommandInvocationInitial("cat", [], [Operand("file.txt")])
    command_type = cat_sig.determine_command_type(inv, [], {})
    result = cat_sig.apply_command_type(command_type, RegularType("hello"))
    assert isinstance(result, InferenceResult)
    assert result.output_type.pattern == ".*"

    # grep with pattern
    inv = CommandInvocationInitial("grep", [], [Operand("abc"), Operand("file.txt")])
    command_type = grep_sig.determine_command_type(inv, [], {})
    result = grep_sig.apply_command_type(command_type, RegularType("hello"))
    assert isinstance(result, InferenceResult)
    # grep output is an intersection containing the pattern
    assert "abc" in (result.output_type.pattern or "")

    # sort -n (output should preserve input)
    inv = CommandInvocationInitial("sort", [Flag("-n")], [])
    command_type = sort_sig.determine_command_type(inv, [], {})
    result = sort_sig.apply_command_type(command_type, RegularType("123"))
    assert isinstance(result, InferenceResult)
    assert result.output_type.pattern == "123"
