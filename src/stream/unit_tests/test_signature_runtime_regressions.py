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


def _apply_signature(signature, input_type, invocation, env_annotations=None):
    if env_annotations is None:
        env_annotations = {}
    command_type = signature.determine_command_type(invocation, [], env_annotations)
    return signature.apply_command_type(command_type, input_type)


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

    result = _apply_signature(sort_signature, RegularType(".+"), invocation)

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
    result = _apply_signature(grep_signature, RegularType(".+"), invocation)

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
    result = _apply_signature(grep_signature, input_type, invocation)

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

    result = _apply_signature(grep_signature, RegularType(".+"), invocation)

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

    command_type = find_signature.determine_command_type(invocation, [], {})
    result = find_signature.apply_command_type(command_type, RegularType(".+"))

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
    malformed_result = _apply_signature(sed_signature, RegularType(".+"), malformed_pattern)
    multi_result = _apply_signature(sed_signature, RegularType(".+"), multi_command)

    assert isinstance(input_type, RegularType)
    assert no_input_type is None
    assert isinstance(malformed_result, InferenceResult)
    assert isinstance(malformed_result.output_type, RegularType)
    assert isinstance(multi_result, InferenceResult)
    assert isinstance(multi_result.output_type, RegularType)
