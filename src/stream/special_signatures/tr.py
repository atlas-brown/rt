import re
from typing import Optional, Tuple
from stream.command_signature import CommandSignature, InferenceResult, inverse_fst_product
from stream.regular_type import RegularType
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from stream.tool_error import ToolError
from stream.transducer import translate_to_line_delimited_FST, translation_FST, product_fst_automaton, compression_FST, deletion_FST
from stream.transducer_utils import compute_fst_automaton_product
# from stream.utils.logger import get_logger

class TrSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations) -> Tuple[RegularType, Optional[RegularType]]:
        input_type, no_input_type = super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type
        set1 = parsed_command_invocation.operand_list[0].name
        # FIXME: handle \012
        if set1 == "\\\\n" or set1 == "\\012" or set1 == "\\\\012":
            return input_type, no_input_type
        
        return input_type, RegularType(get_output_pattern(parsed_command_invocation), tainted=False)

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        # Classify the last detailed command invocation as supported
        # get_logger().classify_last_invocation_as_supported()
        supported_flags = set(["-c", "-d", "-s", "-t"])
        
        # Record command pattern based on flag combination
        # flag_pattern = get_logger().get_flag_pattern_from_invocation(parsed_command_invocation)
        # get_logger().add_command_pattern_log("tr", flag_pattern)

        # NOTE(logger-state): output_type/precision stored for downstream type summaries.
        # get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = False
        # FIXME: may have some issues
        set1 = parsed_command_invocation.operand_list[0].name
        set1 = preprocess_set(set1)
        parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
        # if parsed_flags.issubset(supported_flags):
        #     get_logger().classify_last_invocation_as_supported()
        # else:
        #     get_logger().classify_last_invocation_as_unsupported()
        
        arg1 = parsed_command_invocation.operand_list[0].name
        arg2 = ""
        if len(parsed_command_invocation.operand_list) > 1:
            arg2 = parsed_command_invocation.operand_list[1].name
        complement = False
        squeeze = False
        if "-s" in parsed_flags:
            squeeze = True
        if "-c" in parsed_flags:
            complement = True
        # get_logger().get_latest_record()["command_list"][-1]["output_type"] = f"translate-chars(α, {refine_log(arg1)}, {refine_log(arg2)}, complement={complement}, squeeze={squeeze})"

        set1 = preprocess_set(arg1)
        set2 = preprocess_set(arg2)
        previous_output_type = previous_output_type.to_full_stream_repr()
        flags = parsed_flags.copy()
        if "-c" in flags:
            set1 = complement_set(set1)
            flags.remove("-c")
        if flags == set():
            fst = translation_FST(set1, set2)
            output_type = RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa), tainted=previous_output_type.tainted, repr_mode="stream")
            return InferenceResult(output_type, inverse_fst_product(fst, previous_output_type.nfa), True)
        if flags == {"-d"}:
            fst = deletion_FST(set1)
            output_type = RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa), tainted=previous_output_type.tainted, repr_mode="stream")
            return InferenceResult(output_type, inverse_fst_product(fst, previous_output_type.nfa), True)
        if flags == {"-s"}:
            if set2 == "":
                fst = compression_FST(set1)
                output_type = RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa), tainted=previous_output_type.tainted, repr_mode="stream")
                return InferenceResult(output_type, inverse_fst_product(fst, previous_output_type.nfa), True)
            else:
                fst1 = translation_FST(set1, set2)
                fst2 = compression_FST(set2)
                output_type = RegularType(automaton=product_fst_automaton(fst2, product_fst_automaton(fst1, previous_output_type.nfa)), tainted=previous_output_type.tainted, repr_mode="stream")
                return InferenceResult(output_type, lambda x: inverse_fst_product(inverse_fst_product(fst2)(x), previous_output_type.nfa), True)
            
        return RegularType(".*")


        if set1 == "\n":
            if len(parsed_command_invocation.operand_list) == 1:
                if "-d" in parsed_flags:
                    output_type = previous_output_type.kleene_plus()
                    # output_type.possible_line_numbers = (0, 1)
                    output_type.tainted = True
                    return output_type.to_one_line_repr()
                if "-s" in parsed_flags:
                    output_type = previous_output_type & RegularType(".+")
                    output_type.tainted = previous_output_type.tainted
                    return output_type
                    
            else:
                set2 = parsed_command_invocation.operand_list[1].name
                set2 = preprocess_set(set2)
                line_type = previous_output_type + (RegularType(f"{re.escape(set2)}") + previous_output_type).kleene_star()
                # line_type.possible_line_numbers = (0, 1)
                line_type.tainted = True
                if "-s" in parsed_flags:
                    fst = compression_FST(set2)
                    output_type = RegularType(automaton=product_fst_automaton(fst, line_type.nfa))
                    # output_type.possible_line_numbers = (0, 1)
                    return output_type.to_one_line_repr()
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
                    return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa), tainted=previous_output_type.tainted)
                else:
                    nfa = product_fst_automaton(fst, previous_output_type.nfa)
                    fst = compression_FST(set2)
                    return RegularType(automaton=product_fst_automaton(fst, nfa), tainted=previous_output_type.tainted)
            else:
                fst = translate_to_line_delimited_FST(set1)
                if "-s" in parsed_flags:
                    output_type = RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa)) & RegularType(".+")
                    output_type.tainted = previous_output_type.tainted
                    return output_type
                return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa), tainted=previous_output_type.tainted)
        
        if "-s" in parsed_flags:
            set1 = parsed_command_invocation.operand_list[0].name
            set1 = preprocess_set(set1)
            if "-c" in parsed_flags:
                set1 = complement_set(set1)
            fst = compression_FST(set1)
            return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa), tainted=previous_output_type.tainted)
        if "-d" in parsed_flags:
            set1 = parsed_command_invocation.operand_list[0].name
            set1 = preprocess_set(set1)
            if "-c" in parsed_flags:
                set1 = complement_set(set1)
            fst = deletion_FST(set1)
            return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa), tainted=previous_output_type.tainted)
        return previous_output_type & RegularType(f"{get_output_pattern(parsed_command_invocation)}")

def replace_POSIX_class(set1: str) -> str:
    set1 = set1.replace("[:lower:]", "a-z")
    set1 = set1.replace("[:upper:]", "A-Z")
    set1 = set1.replace("[:alpha:]", "a-zA-Z")
    set1 = set1.replace("[:punct:]", "!-/:-@[-`{-~")
    set1 = set1.replace("[:digit:]", "0-9")
    set1 = set1.replace("[:alnum:]", "a-zA-Z0-9")
    set1 = set1.replace("[:blank:]", " \t")
    set1 = set1.replace("[:space:]", " \t\r\n\v\f")
    return set1

def expand_ranges(input_set: str) -> str:
    result = input_set
    exists_dash = False
    # FIXME: handle - character in set
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

def complement_set(input_set: str) -> str:
    result = ""
    for i in range(256):
        if chr(i) not in input_set:
            result += chr(i)
    if result == "":
        raise ToolError("Invalid set for tr (empty complement)")
    return result

def preprocess_set(set1: str) -> str:
    set1 = set1.replace("\\\\", "\\")
    # FIXME: handle \012
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
    set1 = re.sub(r"([[\]])", r"\\\1", set1)
    if "-c" in parsed_flags:
        return f"[{set1}]*"

    return f"~(.*[{set1}].*)"

def refine_log(s: str) -> str:
    if s == " ":
        return "\" \""
    if s == "":
        return "\"\""
    return s
