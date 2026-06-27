import re
from typing import Optional, Tuple

from stream.command_signature import CommandSignature
from stream.command_type import PolymorphicCommandType, SimpleCommandType
from stream.char_set_utils import replace_POSIX_class
from stream.regular_type import RegularType
from stream.transformation_ast import ALPHA, ConstantTransform, DeleteCharsTransform, TranslateCharsTransform
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from stream.tool_error import ToolError

class TrSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations) -> Tuple[RegularType, Optional[RegularType]]:
        input_type, no_input_type = super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type
        set1 = parsed_command_invocation.operand_list[0].name
        if set1 == "\\\\n" or set1 == "\\012" or set1 == "\\\\012":
            return input_type, no_input_type
        
        return input_type, RegularType(get_output_pattern(parsed_command_invocation), tainted=False)

    def construct_command_type(self, parsed_command_invocation, env_annotations):
        parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
        if len(parsed_command_invocation.operand_list) == 0:
            return SimpleCommandType(RegularType(".*"), RegularType(".*"), self_contained=True)

        arg1 = parsed_command_invocation.operand_list[0].name
        arg2 = parsed_command_invocation.operand_list[1].name if len(parsed_command_invocation.operand_list) > 1 else ""
        set1 = preprocess_set(arg1)
        set2 = preprocess_set(arg2)
        invert = "-c" in parsed_flags
        flags = parsed_flags - {"-c"}

        if flags == set():
            transform = TranslateCharsTransform(
                ALPHA,
                set1,
                set2,
                invert=invert,
                approximate_when_fst_disabled=True,
                preprocessed=True,
            )
        elif flags == {"-d"}:
            transform = DeleteCharsTransform(
                ALPHA,
                set1,
                invert=invert,
                approximate_when_fst_disabled=True,
                preprocessed=True,
            )
        elif flags == {"-s"}:
            target = set2 if set2 else set1
            transform = TranslateCharsTransform(
                ALPHA,
                set1,
                target,
                invert=invert,
                squeeze=True,
                approximate_when_fst_disabled=True,
                preprocessed=True,
            )
        else:
            transform = ConstantTransform(RegularType(".*"))

        return PolymorphicCommandType(transform, self_contained=True)

def expand_ranges(input_set: str) -> str:
    result = input_set
    exists_dash = False
    while "-" in result:
        index = result.index("-")
        if index == 0:
            raise ToolError("Invalid set for tr (invalid range)")
        if index == len(result) - 1:
            exists_dash = True
            result = result[:-1]
            continue
        start = result[index - 1]
        end = result[index + 1]
        if ord(start) >= ord(end):
            raise ToolError("Invalid set for tr (invalid range)")
        new_result = ""
        if index > 1:
            new_result += result[:index - 1]
        added_set = "".join(map(chr, range(ord(start), ord(end) + 1)))
        if "-" in added_set:
            exists_dash = True
            added_set = added_set.replace("-", "")
        new_result += added_set
        if index < len(result) - 2:
            new_result += result[index + 2:]
        result = new_result
    if exists_dash:
        result += "-"
    return result

def preprocess_set(set1: str) -> str:
    set1 = set1.replace("\\\\", "\\")
    set1 = set1.replace("\\\\012", "\n")
    set1 = set1.replace("\\012", "\n")
    escape_dict = {
        'n': '\n',
        't': '\t',
        'r': '\r',
        'v': '\v',
        'f': '\f',
        'b': '\b',
        's': ' ',
        '+': '+',
        '{': '{',
        '}': '}',
        '|': '|',
        '&': '&',
        '~': '~',
        '*': '*',
        '?': '?',
        '.': '.',
        '^': '^',
        '$': '$',
        '(': '(',
        ')': ')',
        '[': '[',
        ']': ']',
        '"': '"',
        "'": "'",
        '-': '-',
        '\\': '\\'
    }
    set1 = re.sub(r'\\([\\ntrvfbs+{}|&~*?.^$()[\]"\']|-)', lambda m: escape_dict[m.group(1)], set1)
    # [\n*] -> \n (handle character set with *)
    set1 = re.sub(r"\[([^*\]]+)\*\]", r"\1", set1)
    return expand_ranges(replace_POSIX_class(set1))


def get_output_pattern(parsed_command_invocation: CommandInvocationInitial) -> str:
    if len(parsed_command_invocation.operand_list) == 0:
        raise ToolError("No pattern provided for tr")
    parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
    if len(parsed_command_invocation.operand_list) == 0:
        raise ToolError("No pattern provided for tr")
    set1 = parsed_command_invocation.operand_list[0].name
    set1 = set1.replace("\\\\", "\\")
    set1 = replace_POSIX_class(set1)
    set1 = re.sub(r"([\[\]])", r"\\\1", set1)
    if "-c" in parsed_flags:
        return f"[{set1}]*"

    return f"~(.*[{set1}].*)"
