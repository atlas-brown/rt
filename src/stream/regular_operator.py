from stream.regex_parser import convert_to_pure_string, convert_to_pure_string_for_ast, is_pure_string_for_ast
from stream.regular_type import RegularType
from stream.transducer import *
from typing import List, Set, Optional, Dict, Tuple, Union, Callable

def preprocess(source_chars: str) -> str:
    """
    source_chars: C
    C: CC | c | POSIX character class | c-c

    return: C'
    C': c | C'C'
    """
    source_chars = replace_POSIX_class(source_chars)
    processed_chars = ""
    contains_dash = False
    i = 0
    if source_chars and source_chars[0] == '-':
        processed_chars += '-'
        i = 1
        
    while i < len(source_chars):
        if source_chars[i] == '-' and i > 0 and i < len(source_chars) - 1:
            start = source_chars[i-1]
            end = source_chars[i+1]
            if ord(start) > ord(end):
                raise ToolError(f"invalid range: {start}-{end}")
            else:
                for char_code in range(ord(start), ord(end) + 1):
                    if chr(char_code) == '-':
                        contains_dash = True
                    else:
                        processed_chars += chr(char_code)
            i += 1
        elif source_chars[i] == '-' and i == len(source_chars) - 1:
            contains_dash = True
        else:
            processed_chars += source_chars[i]
        i += 1
    
    if contains_dash:
        processed_chars += '-'
    
    processed_chars = process_escape_chars(processed_chars)
    return processed_chars

def replace_POSIX_class(source_chars: str) -> str:
    source_chars = source_chars.replace("[:lower:]", "a-z")
    source_chars = source_chars.replace("[:upper:]", "A-Z")
    source_chars = source_chars.replace("[:alpha:]", "a-zA-Z")
    source_chars = source_chars.replace("[:punct:]", "!-/:-@[-`{-~")
    source_chars = source_chars.replace("[:digit:]", "0-9")
    source_chars = source_chars.replace("[:alnum:]", "a-zA-Z0-9")
    source_chars = source_chars.replace("[:blank:]", " \t")
    source_chars = source_chars.replace("[:word:]", "a-zA-Z0-9_")
    source_chars = source_chars.replace("[:xdigit:]", "0-9a-fA-F")
    source_chars = source_chars.replace("[:space:]", " \t\n\r\f\v")
    return source_chars

def process_escape_chars(source_chars: str) -> str:
    source_chars = source_chars.replace("\\\\", "\\")
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
    source_chars = re.sub(r'\\([\\ntrvfbs+{}|&~*?.^$()[\]"\']|-)', lambda m: escape_dict[m.group(1)], source_chars)
    return source_chars
    
def complement_set(source_chars: str) -> str:
    result = ""
    for i in range(256):
        if chr(i) not in source_chars:
            result += chr(i)
    if result == "":
        raise ToolError("Invalid set for tr (empty complement)")
    return result

def reverse(input_type: RegularType) -> RegularType:
    return input_type.reverse()

def translate_chars(input_type: RegularType, source_chars: str, target_chars: str, invert: bool = False, squeeze: bool = False) -> RegularType:
    """
    source_chars, target_chars: C
    C: CC | c | POSIX character class | c-c
    """

    source_chars = preprocess(source_chars)
    target_chars = preprocess(target_chars)
    if invert:
        source_chars = complement_set(source_chars)
    fst = translation_FST(source_chars, target_chars)
    input_automaton = input_type.nfa
    output_automaton = product_fst_automaton(fst, input_automaton)
    if squeeze:
        fst = compression_FST(target_chars)
        output_automaton = product_fst_automaton(fst, output_automaton)
    return RegularType(automaton=output_automaton)

def field_select(input_type: RegularType, delimiter: str, field_indices: str, invert: bool = False) -> RegularType:
    """
    delimiter: C
    C: CC | c | POSIX character class | c-c

    field_indices: N
    N: n | n-n | n- | N,N
    """
    def parse_field_indices(indices: str) -> Tuple[List[int], bool]:
        """Parse field indices into a list of integers and flag for unbounded ranges."""
        if not indices:
            return [], False
            
        result = []
        unbounded = False
        unbounded_start = float('inf')
        
        for part in indices.split(','):
            if '-' not in part:
                # Simple number case
                try:
                    result.append(int(part))
                    continue
                except ValueError:
                    raise ToolError(f"Invalid field number: {part}")
                    
            # Handle range
            range_parts = part.split('-')
            if len(range_parts) != 2:
                raise ToolError(f"Invalid range format: {part}")
                
            start, end = range_parts
            start = 1 if not start else start
            
            try:
                start = int(start)
                if not end:  # Unbounded range (n-)
                    unbounded = True
                    unbounded_start = min(unbounded_start, start)
                else:  # Bounded range (n-m)
                    end = int(end)
                    if start > end:
                        raise ToolError(f"Invalid range: start {start} > end {end}")
                    result.extend(range(start, end + 1))
            except ValueError:
                raise ToolError(f"Invalid range values: {part}")
        
        # Handle unbounded range if present
        if unbounded:
            result = [x for x in result if x < unbounded_start]
            result.extend([unbounded_start, -1])
            
        return result, unbounded

    # Process delimiter and field indices
    if delimiter:
        delimiter = preprocess(delimiter)
        
    fields, has_unbounded_range = parse_field_indices(field_indices)
    
    # Handle field inversion if requested
    if invert:
        if not fields:
            raise ToolError("Cannot invert empty field selection")
            
        inverted_fields = []
        if has_unbounded_range:
            # For unbounded ranges, invert means selecting fields 1 to (unbounded_start-1)
            upper_bound = fields[-2]
            inverted_fields = list(range(1, upper_bound))
            has_unbounded_range = False
        else:
            # For bounded ranges, invert means selecting all fields not in the original set
            max_field = max(fields)
            field_set = set(fields)
            for i in range(1, max_field + 1):
                if i not in field_set:
                    inverted_fields.append(i)
            # Add unbounded range after the max field
            inverted_fields.extend([max_field + 1, -1])
            has_unbounded_range = True
            
        fields = inverted_fields
    
    # Process automation based on field selection
    input_automaton = input_type.nfa
    
    if has_unbounded_range:
        if len(fields) > 2:
            # Handle fields before unbounded range
            normal_fields = fields[:-2]
            unbounded_start = fields[-2]
            
            if delimiter:
                fst1 = cut_field_FST(delimiter, normal_fields)
                fst2 = cut_field_no_upperbound_FST(delimiter, unbounded_start, leading_delimiter=True)
            else:
                fst1 = cut_char_FST(normal_fields)
                fst2 = cut_char_no_upperbound_FST(unbounded_start)
            
            output_automaton = product_fst_automaton(fst1, input_automaton)
            output_automaton = product_fst_automaton(fst2, input_automaton)
        else:
            # Only unbounded range
            unbounded_start = fields[0]
            if delimiter:
                fst = cut_field_no_upperbound_FST(delimiter, unbounded_start, leading_delimiter=False)
            else:
                fst = cut_char_no_upperbound_FST(unbounded_start)
            output_automaton = product_fst_automaton(fst, input_automaton)
    else:
        # Simple field selection
        if delimiter:
            fst = cut_field_FST(delimiter, fields)
        else:
            fst = cut_char_FST(fields)
        output_automaton = product_fst_automaton(fst, input_automaton)
        
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
        
