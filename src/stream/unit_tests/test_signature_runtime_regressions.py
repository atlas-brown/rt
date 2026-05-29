from pash_annotations.datatypes.BasicDatatypes import Flag, Operand, Option
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from stream.command_signature import InferenceResult
from stream.regular_type import RegularType
from stream.signature_loader import SignatureLoader


def _lookup_signature(command_name: str):
    SignatureLoader.reset_instance()
    loader = SignatureLoader.get_instance("./src/stream/signatures")
    for signature in loader.signatures:
        if signature.command_name == command_name:
            return signature
    raise AssertionError(f"missing signature for {command_name}")


def test_sort_allows_leading_option_like_operands_without_parser_crash():
    sort_signature = _lookup_signature("sort")
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

    result = sort_signature.determine_output_type(RegularType(".+"), invocation, [], {})

    assert isinstance(result, InferenceResult)
    assert isinstance(result.output_type, RegularType)


def test_grep_f_file_without_pattern_operand_falls_back_without_index_error():
    grep_signature = _lookup_signature("grep")
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
    result = grep_signature.output_type_inference(RegularType(".+"), invocation, {})

    assert isinstance(input_type, RegularType)
    assert no_input_type is None
    assert isinstance(result, InferenceResult)
    assert isinstance(result.output_type, RegularType)


def test_grep_combined_fw_file_keeps_input_type():
    grep_signature = _lookup_signature("grep")
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
    result = grep_signature.output_type_inference(input_type, invocation, {})

    assert isinstance(expected_input_type, RegularType)
    assert no_input_type is None
    assert isinstance(result, InferenceResult)
    assert result.output_type.is_subtype(input_type)[0]
    assert input_type.is_subtype(result.output_type)[0]


def test_grep_e_pattern_from_operands_initializes_pattern_type_string():
    grep_signature = _lookup_signature("grep")
    invocation = CommandInvocationInitial(
        "grep",
        [Flag("-e")],
        [Operand("^v")],
    )

    result = grep_signature.output_type_inference(RegularType(".+"), invocation, {})

    assert isinstance(result, InferenceResult)
    assert isinstance(result.output_type, RegularType)


def test_find_exec_ls_unwraps_nested_inference_result():
    find_signature = _lookup_signature("find")
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

    result = find_signature.output_type_inference(RegularType(".+"), invocation, {})

    assert isinstance(result, InferenceResult)
    assert isinstance(result.output_type, RegularType)


def test_sed_falls_back_for_complex_patterns_and_multi_command_operands():
    sed_signature = _lookup_signature("sed")

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
    malformed_result = sed_signature.output_type_inference(RegularType(".+"), malformed_pattern, {})
    multi_result = sed_signature.output_type_inference(RegularType(".+"), multi_command, {})

    assert isinstance(input_type, RegularType)
    assert no_input_type is None
    assert isinstance(malformed_result, InferenceResult)
    assert isinstance(malformed_result.output_type, RegularType)
    assert isinstance(multi_result, InferenceResult)
    assert isinstance(multi_result.output_type, RegularType)
