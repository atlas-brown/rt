from stream.char_set_utils import complement_set, preprocess_char_set
from stream.regex_parser import convert_to_pure_string, convert_to_pure_string_for_ast, is_pure_string_for_ast
from stream.regular_type import RegularType
from stream.transducer import *
from typing import List, Set, Optional, Dict, Tuple, Union, Callable

def translate_chars(input_type: RegularType, source_chars: str, target_chars: str, invert: bool = False, squeeze: bool = False) -> RegularType:
    """
    source_chars, target_chars: C
    C: CC | c | POSIX character class | c-c
    """

    source_chars = preprocess_char_set(source_chars)
    target_chars = preprocess_char_set(target_chars)
    if invert:
        source_chars = complement_set(source_chars)
    fst = translation_FST(source_chars, target_chars)
    input_automaton = input_type.nfa
    output_automaton = product_fst_automaton(fst, input_automaton)
    if squeeze:
        fst = compression_FST(target_chars)
        output_automaton = product_fst_automaton(fst, output_automaton)
    return RegularType(automaton=output_automaton)

def translate_match(
    input_type: RegularType,
    pattern: str | RegularType,
    replacement: str,
    global_match: bool = False,
    mode: str = "compat",
) -> RegularType:
    original_pattern = None
    if isinstance(pattern, str):
        original_pattern = pattern
        pattern = RegularType(pattern, mode)
    if is_pure_string_for_ast(pattern.ast):
        s1 = convert_to_pure_string_for_ast(pattern.ast)
        if global_match:
            fst = global_replacement_FST(s1, replacement)
        else:
            fst = first_replacement_FST(s1, replacement)
        output_automaton = product_fst_automaton(fst, input_type.nfa)
        return RegularType(automaton=output_automaton)
    else:
        if original_pattern:
            if original_pattern.startswith("^") and original_pattern.endswith("$"):
                fst = start_regex_replacement_FST(RegularType(".*").nfa, replacement)
                input_typ1 = input_type & pattern
                input_typ2 = input_type - pattern
                output_automaton = product_fst_automaton(fst, input_typ1.nfa)
                return RegularType(automaton=output_automaton) | input_typ2
            elif original_pattern.startswith("^"):
                fst = start_regex_replacement_FST(pattern.nfa, replacement)
                output_automaton = product_fst_automaton(fst, input_type.nfa)
                return RegularType(automaton=output_automaton)
            elif original_pattern.endswith("$"):
                end_pattern = original_pattern[:-2]
                automata = RegularType(end_pattern, mode).reverse().nfa
                fst = start_regex_replacement_FST(automata, replacement[::-1])
                output_automaton = product_fst_automaton(fst, input_type.reverse().nfa)
                return RegularType(automaton=output_automaton).reverse()
        if global_match:
            fst = global_regex_replacement_FST(pattern.nfa, replacement)
            output_automaton = product_fst_automaton(fst, input_type.nfa)
            output_type = RegularType(automaton=output_automaton)
        else:
            fst = first_regex_replacement_FST(pattern.nfa, replacement)
            output_automaton = product_fst_automaton(fst, input_type.nfa)
            output_type = RegularType(automaton=output_automaton)
        return output_type
    

def line_extract(input_type: RegularType, pattern: str | RegularType) -> RegularType:
    original_pattern = None
    if isinstance(pattern, str):
        original_pattern = pattern
        pattern = RegularType(pattern)
    if is_pure_string_for_ast(pattern.ast):
        if (input_type & (RegularType(".*") + pattern + RegularType(".*"))).is_empty():
            return RegularType("")
        else:
            return pattern
    else:
        if original_pattern:
            if original_pattern.startswith("^") and original_pattern.endswith("$"):
                return input_type & pattern
            elif original_pattern.startswith("^"):
                fst = start_regex_extract_FST(pattern.nfa)
                output_automaton = product_fst_automaton(fst, input_type.nfa)
                return RegularType(automaton=output_automaton)
            elif original_pattern.endswith("$"):
                fst = start_regex_extract_FST(pattern.reverse().nfa)
                output_automaton = product_fst_automaton(fst, input_type.reverse().nfa)
                return RegularType(automaton=output_automaton).reverse()
        fst = global_regex_extract_FST(pattern.nfa)
        output_automaton = product_fst_automaton(fst, input_type.nfa)
        return RegularType(automaton=output_automaton)
        
