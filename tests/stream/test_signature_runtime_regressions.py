from pash_annotations.datatypes.BasicDatatypes import Flag, Operand, Option
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from stream.regular_type import RegularType


def test_sort_allows_leading_option_like_operands_without_parser_crash(
    lookup_signature,
    apply_signature,
):
    sort_signature = lookup_signature("sort")
    invocation = CommandInvocationInitial(
        "sort",
        [],
        [
            Operand("--parallel=${threads}"),
            Operand("-T"),
            Operand("."),
            Operand("-k"),
            Operand("1,1"),
        ],
    )

    result = apply_signature(sort_signature, RegularType(".+"), invocation)

    assert isinstance(result, RegularType)
    assert isinstance(result, RegularType)


def test_grep_f_file_without_pattern_operand_falls_back_without_index_error(
    lookup_signature,
    apply_signature,
):
    grep_signature = lookup_signature("grep")
    invocation = CommandInvocationInitial(
        "grep",
        [Option("-f", "stopwords.txt"), Flag("-v"), Flag("-w"), Flag("-F")],
        [],
    )

    input_type, no_input_type = grep_signature.get_input_type(
        invocation,
        ["no_meaningless_command"],
        {},
    )
    result = apply_signature(grep_signature, RegularType(".+"), invocation)

    assert isinstance(input_type, RegularType)
    assert no_input_type is None
    assert isinstance(result, RegularType)
    assert isinstance(result, RegularType)


def test_grep_combined_fw_file_keeps_input_type(lookup_signature, apply_signature):
    grep_signature = lookup_signature("grep")
    invocation = CommandInvocationInitial(
        "grep",
        [Option("-f", "-w")],
        [Operand("dict.txt")],
    )
    input_type = RegularType("[A-Z]*")

    expected_input_type, no_input_type = grep_signature.get_input_type(
        invocation,
        ["no_meaningless_command"],
        {},
    )
    result = apply_signature(grep_signature, input_type, invocation)

    assert isinstance(expected_input_type, RegularType)
    assert no_input_type is None
    assert isinstance(result, RegularType)
    assert result.is_subtype(input_type)[0]
    assert input_type.is_subtype(result)[0]


def test_grep_e_pattern_from_operands_initializes_pattern_type_string(lookup_signature, apply_signature):
    grep_signature = lookup_signature("grep")
    invocation = CommandInvocationInitial(
        "grep",
        [Flag("-e")],
        [Operand("^v")],
    )

    result = apply_signature(grep_signature, RegularType(".+"), invocation)

    assert isinstance(result, RegularType)
    assert isinstance(result, RegularType)


def test_constructed_command_type_carries_input_constraints(lookup_signature):
    whoami_signature = lookup_signature("whoami")
    whoami_type = whoami_signature.determine_command_type(
        CommandInvocationInitial("whoami", [], []),
        [],
        {},
        ["no_ignored_input"],
    )

    assert whoami_type.input_type.pattern == ""
    assert whoami_type.no_input_type is None

    sort_signature = lookup_signature("sort")
    sort_type = sort_signature.determine_command_type(
        CommandInvocationInitial("sort", [], []),
        [],
        {},
        ["no_sort_non_numeric_with_numeric_input"],
    )

    assert isinstance(sort_type.input_type, RegularType)
    assert isinstance(sort_type.no_input_type, RegularType)


def test_find_exec_ls_unwraps_nested_inference_result(lookup_signature):
    find_signature = lookup_signature("find")
    invocation = CommandInvocationInitial(
        "find",
        [],
        [
            Operand("/workspace"),
            Operand("-e"),
            Operand("-x"),
            Operand("-e"),
            Operand("-c"),
            Operand("ls"),
            Operand("-l"),
            Operand("{}"),
            Operand("+"),
        ],
    )

    command_type = find_signature.determine_command_type(invocation, [], {})
    result = find_signature.apply_command_type(command_type, RegularType(".+"))

    assert isinstance(result, RegularType)
    assert isinstance(result, RegularType)


def test_sed_falls_back_for_complex_patterns_and_multi_command_operands(
    lookup_signature,
    apply_signature,
):
    sed_signature = lookup_signature("sed")

    malformed_pattern = CommandInvocationInitial(
        "sed",
        [],
        [Operand(r"s,^[^\,]*\,\(.*\),\1,")],
    )
    multi_command = CommandInvocationInitial(
        "sed",
        [],
        [Operand(r"s/ /\\ /g;s/^/pushd -q /;1!G;h;\$!d;")],
    )

    input_type, no_input_type = sed_signature.get_input_type(
        malformed_pattern,
        ["no_meaningless_command"],
        {},
    )
    malformed_result = apply_signature(
        sed_signature, RegularType(".+"), malformed_pattern
    )
    multi_result = apply_signature(sed_signature, RegularType(".+"), multi_command)

    assert isinstance(input_type, RegularType)
    assert no_input_type is None
    assert isinstance(malformed_result, RegularType)
    assert isinstance(malformed_result, RegularType)
    assert isinstance(multi_result, RegularType)
    assert isinstance(multi_result, RegularType)
