import re
from typing import Optional, Tuple
from stream.command_signature import CommandSignature
from stream.regular_type import RegularType
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from stream.tool_error import ToolError
from stream.transducer import translate_to_line_delimited_FST, translation_FST, product_fst_automaton, compression_FST, deletion_FST

class TrSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations) -> Tuple[RegularType, Optional[RegularType]]:
        input_type, no_input_type = super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type
        set1 = parsed_command_invocation.operand_list[0].name
        if set1 == "\\\\n":
            return input_type, no_input_type
        
        return input_type, RegularType(get_output_pattern(parsed_command_invocation))

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        # FIXME: may have some issues
        set1 = parsed_command_invocation.operand_list[0].name
        set1 = preprocess_set(set1)
        parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
        if set1 == "\n":
            if len(parsed_command_invocation.operand_list) == 1:
                if "-d" in parsed_flags:
                    return previous_output_type.kleene_plus()
                if "-s" in parsed_flags:
                    return previous_output_type & RegularType(".+")
            else:
                set2 = parsed_command_invocation.operand_list[1].name
                set2 = preprocess_set(set2)
                line_type = previous_output_type + (RegularType(f"{re.escape(set2)}") + previous_output_type).kleene_star()
                if "-s" in parsed_flags:
                    fst = compression_FST(set2)
                    return RegularType(automaton=product_fst_automaton(fst, line_type.nfa))
                return line_type

        if len(parsed_command_invocation.operand_list) == 2:
            # FIXME: handle flags
            set2 = parsed_command_invocation.operand_list[1].name
            set2 = preprocess_set(set2)
            if "-c" in parsed_flags:
                set1 = complement_set(set1)
            if set2 != "\n":
                fst = translation_FST(set1, set2)
                if "-s" not in parsed_flags:
                    return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa))
                else:
                    nfa = product_fst_automaton(fst, previous_output_type.nfa)
                    fst = compression_FST(set2)
                    return RegularType(automaton=product_fst_automaton(fst, nfa))
            else:
                fst = translate_to_line_delimited_FST(set1)
                if "-s" in parsed_flags:
                    return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa)) & RegularType(".+")
                return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa))
        
        if "-s" in parsed_flags:
            set1 = parsed_command_invocation.operand_list[0].name
            set1 = preprocess_set(set1)
            if "-c" in parsed_flags:
                set1 = complement_set(set1)
            fst = compression_FST(set1)
            return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa))
        if "-d" in parsed_flags:
            set1 = parsed_command_invocation.operand_list[0].name
            set1 = preprocess_set(set1)
            if "-c" in parsed_flags:
                set1 = complement_set(set1)
            fst = deletion_FST(set1)
            return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa))
        return previous_output_type & RegularType(f"{get_output_pattern(parsed_command_invocation)}")

def replace_POSIX_class(set1: str) -> str:
    set1 = set1.replace("[:lower:]", "a-z")
    set1 = set1.replace("[:upper:]", "A-Z")
    set1 = set1.replace("[:alpha:]", "a-zA-Z")
    set1 = set1.replace("[:punct:]", "!-/:-@[-`{-~")
    set1 = set1.replace("[:digit:]", "0-9")
    set1 = set1.replace("[:alnum:]", "a-zA-Z0-9")
    set1 = set1.replace("[:space:]", " \t\n")
    return set1

def expand_ranges(input_set: str) -> str:
    result = input_set
    exists_dash = False
    # FIXME: handle - character in set
    while "-" in result:
        index = result.index("-")
        if index == 0 or index == len(result) - 1:
            raise ToolError("Invalid set for tr (invalid range)")
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

def complement_set(input_set: str) -> str:
    result = ""
    for i in range(128):
        if chr(i) not in input_set:
            result += chr(i)
    if result == "":
        raise ToolError("Invalid set for tr (empty complement)")
    return result

def preprocess_set(set1: str) -> str:
    set1 = set1.replace("\\\\", "\\")
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
    set1 = re.sub(r"([[\]])", r"\\\1", set1)
    if "-c" in parsed_flags:
        return f"[{set1}]*"

    return f"~(.*[{set1}].*)"