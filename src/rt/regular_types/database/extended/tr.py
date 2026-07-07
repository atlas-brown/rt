import re

from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import (
    CharTranslation,
    Constant,
    DeleteChars,
    Input,
)
from rt.regular_types.stream_type import StreamType, _replace_posix_class


class TrResolver(RuleResolver):

    def _resolve_input_type(self, invocation, env, heuristic_rules=None):
        input_type, no_input_type = self._match_input_type(
            {fo.get_name() for fo in invocation.flag_option_list}
        )
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type
        set1 = invocation.operand_list[0].name
        if set1 == "\\\\n" or set1 == "\\012" or set1 == "\\\\012":
            return input_type, no_input_type

        return input_type, StreamType(
            automaton=StreamType.from_pattern(get_output_pattern(invocation)).automaton
        )

    def resolve(
        self, invocation, user_annotations=None, env=None, heuristic_rules=None
    ):
        parsed_flags = set(
            map(lambda flag_option: flag_option.get_name(), invocation.flag_option_list)
        )
        if len(invocation.operand_list) == 0:
            return CommandType.simple(
                StreamType.from_pattern(".*"),
                StreamType.from_pattern(".*"),
            )

        arg1 = invocation.operand_list[0].name
        arg2 = (
            invocation.operand_list[1].name if len(invocation.operand_list) > 1 else ""
        )
        set1 = preprocess_set(arg1)
        set2 = preprocess_set(arg2)
        invert = "-c" in parsed_flags
        flags = parsed_flags - {"-c"}

        if flags == set():
            transform = CharTranslation(Input(), set1, set2, invert, False)
        elif flags == {"-d"}:
            transform = DeleteChars(Input(), set1, invert, preprocessed=True)
        elif flags == {"-s"}:
            target = set2 if set2 else set1
            transform = CharTranslation(Input(), set1, target, invert, True)
        else:
            transform = Constant(StreamType.from_pattern(".*"))

        return CommandType(None, transform)


def expand_ranges(input_set: str) -> str:
    result = input_set
    exists_dash = False
    while "-" in result:
        index = result.index("-")
        if index == 0:
            raise ValueError("Invalid set for tr (invalid range)")
        if index == len(result) - 1:
            exists_dash = True
            result = result[:-1]
            continue
        start = result[index - 1]
        end = result[index + 1]
        if ord(start) >= ord(end):
            raise ValueError("Invalid set for tr (invalid range)")
        new_result = ""
        if index > 1:
            new_result += result[: index - 1]
        added_set = "".join(map(chr, range(ord(start), ord(end) + 1)))
        if "-" in added_set:
            exists_dash = True
            added_set = added_set.replace("-", "")
        new_result += added_set
        if index < len(result) - 2:
            new_result += result[index + 2 :]
        result = new_result
    if exists_dash:
        result += "-"
    return result


def preprocess_set(set1: str) -> str:
    set1 = set1.replace("\\\\", "\\")
    set1 = set1.replace("\\\\012", "\n")
    set1 = set1.replace("\\012", "\n")
    escape_dict = {
        "n": "\n",
        "t": "\t",
        "r": "\r",
        "v": "\v",
        "f": "\f",
        "b": "\b",
        "s": " ",
        "+": "+",
        "{": "{",
        "}": "}",
        "|": "|",
        "&": "&",
        "~": "~",
        "*": "*",
        "?": "?",
        ".": ".",
        "^": "^",
        "$": "$",
        "(": "(",
        ")": ")",
        "[": "[",
        "]": "]",
        '"': '"',
        "'": "'",
        "-": "-",
        "\\": "\\",
    }
    set1 = re.sub(
        r'\\([\\ntrvfbs+{}|&~*?.^$()[\]"\']|-)', lambda m: escape_dict[m.group(1)], set1
    )
    set1 = re.sub(r"\[([^*\]]+)\*\]", r"\1", set1)
    return expand_ranges(_replace_posix_class(set1))


def get_output_pattern(invocation: CommandInvocationInitial) -> str:
    if len(invocation.operand_list) == 0:
        raise ValueError("No pattern provided for tr")
    parsed_flags = set(
        map(lambda flag_option: flag_option.get_name(), invocation.flag_option_list)
    )
    if len(invocation.operand_list) == 0:
        raise ValueError("No pattern provided for tr")
    set1 = invocation.operand_list[0].name
    set1 = set1.replace("\\\\", "\\")
    set1 = _replace_posix_class(set1)
    set1 = re.sub(r"([\[\]])", r"\\\1", set1)
    if "-c" in parsed_flags:
        return f"[{set1}]*"

    return f"~(.*[{set1}].*)"


resolve = TrResolver
