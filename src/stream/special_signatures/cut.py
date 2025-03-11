import re
from typing import Optional, Tuple
from command_signature import CommandSignature
from stream.regex_parser import convert_to_pure_string
from stream.regular_type import RegularType
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from stream.tool_error import ToolError
from stream.transducer import cut_char_FST, cut_char_no_upperbound_FST, cut_field_FST, cut_field_no_upperbound_FST, product_fst_automaton
from stream.user_annotation import AnnotationType

class CutSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations) -> Tuple[RegularType, Optional[RegularType]]:
        if len(parsed_command_invocation.operand_list) > 0 and "no_ignored_input" in heuristic_rules:
            return RegularType(""), None
        
        flags = set()
        flag_args = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, 'get_arg') and flag.get_arg():
                flag_args[name] = flag.get_arg()

        delimiter = "\t"
        if '-d' in flags:
            delimiter = f"{flag_args['-d']}"

        while (delimiter[0] == "(" and delimiter[-1] == ")") or (delimiter[0] == "[" and delimiter[-1] == "]") or (delimiter[0] == "'" and delimiter[-1] == "'") or (delimiter[0] == '"' and delimiter[-1] == '"'):
            delimiter = delimiter[1:-1]
        delimiter = delimiter[-1] # \" -> "

        if '-f' in flags:
            args: list[str] = re.split(",|-", flag_args.get('-f'))
            if len(args) == 0:
                raise ToolError(f"invalid field number arguments: {args}")
            new_args = []
            for arg in args:
                if "${" in arg or "$(" in arg:
                    new_args.append(-1)
                elif arg == "":
                    pass
                elif not arg.isdigit():
                    raise ToolError(f"invalid field number: {arg} in {args} in command cut")
                else:
                    new_args.append(int(arg))
            args = new_args
            field_num = max(args)
            # every arg is a variable or default value
            if field_num == -1:
                return RegularType(".*"), None
            if field_num < 1:
                raise ToolError(f"field number must be greater than 0: {field_num}")
            if field_num == 1:
                if "no_meaningless_command" not in heuristic_rules:
                    return RegularType(".*"), None
                else:
                    return RegularType(".*"), RegularType("[^" + delimiter + "]*")
            
            pattern = f"[^{delimiter}]*({re.escape(delimiter)}[^{delimiter}]*){{0,{field_num-2}}}"
            if "no_meaningless_command" not in heuristic_rules:
                return RegularType(".*"), None
            else:
                return RegularType(".*"), RegularType(pattern)
            
        return super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)

    def output_type_inference(self, previous_output_type: RegularType, parsed_command_invocation: CommandInvocationInitial, env_annotations) -> RegularType:
        if len(parsed_command_invocation.operand_list) > 0:
            file_name = parsed_command_invocation.operand_list[0].name
            if any(annotation.annotation_type == AnnotationType.FILE for annotation in env_annotations.get(file_name, [])):
                for annotation in env_annotations.get(file_name, []):
                    if annotation.annotation_type == AnnotationType.FILE:
                        previous_output_type = RegularType(annotation.pattern)
                        break
            else:
                previous_output_type = RegularType(".*")
        flags = set()
        flag_args = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, 'get_arg') and flag.get_arg():
                flag_args[name] = flag.get_arg()

        if "-b" in flags or "-c" in flags:
            args1 = preprocess(flag_args.get('-c'))
            args2 = preprocess(flag_args.get('-b'))
            args = args1 + args2
            if len(args) == 0:
                return RegularType(".*")
            if args[-1] == -1:
                if len(args) == 2:
                    fst = cut_char_no_upperbound_FST(args[-2])
                    return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa))
                fst1 = cut_char_FST(args[:-2])
                fst2 = cut_char_no_upperbound_FST(args[-2])
                return RegularType(automaton=product_fst_automaton(fst1, previous_output_type.nfa)) + RegularType(automaton=product_fst_automaton(fst2, previous_output_type.nfa))
            fst = cut_char_FST(args)
            return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa))

        delimiter = "\t"
        if '-d' in flags:
            delimiter = f"{flag_args['-d']}"

        while (delimiter[0] == "(" and delimiter[-1] == ")") or (delimiter[0] == "[" and delimiter[-1] == "]") or (delimiter[0] == "'" and delimiter[-1] == "'") or (delimiter[0] == '"' and delimiter[-1] == '"'):
            delimiter = delimiter[1:-1]
        delimiter = delimiter[-1] # \" -> "

        if '-f' in flags:
            args = preprocess(flag_args.get('-f'))
            if len(args) == 0:
                return RegularType(".*")
            if args[-1] == -1:
                if len(args) == 2:
                    fst = cut_field_no_upperbound_FST(delimiter, args[-2])
                    return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa))
                fst1 = cut_field_FST(delimiter, args[:-2])
                fst2 = cut_field_no_upperbound_FST(delimiter, args[-2], leading_delimiter=True)
                return RegularType(automaton=product_fst_automaton(fst1, previous_output_type.nfa)) + RegularType(automaton=product_fst_automaton(fst2, previous_output_type.nfa))
            fst = cut_field_FST(delimiter, args)
            return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa))

        
        return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        # if '-f' in flags:
        #     field_num = int(flag_args.get('-f', '1'))
        #     pattern = previous_output_type.pattern
            
        #     field_patterns = re.split(delimiter, pattern)
        #     if field_num <= len(field_patterns):
        #         return RegularType(field_patterns[field_num - 1])
        #     raise ValueError(f"when cutting by field number, the field number must be less than or equal to the number of fields in the input: {field_num} > {len(field_patterns)}")
            
        # return super().inference_output_type(previous_output_type, parsed_command_node)

def preprocess(arg: str) -> list[int]:
    # 1- -> 1, -1
    # -2 -> 1, 2
    # 1-3 -> 1, 2, 3
    # 1, 3 -> 1, 3
    if not arg:
        return []
    
    if "${" in arg or "$(" in arg:
        return []
        
    result = []
    parts = arg.split(',')
    no_upper_bound = False
    no_upper_bound_start = 1000000
        
    for part in parts:
        if "-" in part:
            range_parts = part.split('-')
            if len(range_parts) != 2:
                raise ToolError(f"invalid range format: {part}")
                
            start, end = range_parts
            if not start:
                start = 1
            if not end:
                no_upper_bound = True
                end = -1
                
            try:
                start, end = int(start), int(end)
                if end == -1:
                    no_upper_bound_start = min(start, no_upper_bound_start)
                else:
                    result.extend(range(start, end + 1))
            except ValueError:
                raise ToolError(f"invalid range values: {part}")
                
        else:
            try:
                result.append(int(part))
            except ValueError:
                raise ToolError(f"invalid field number: {part}")
    if no_upper_bound:
        result = [x for x in result if x < no_upper_bound_start]
        result.extend([no_upper_bound_start, -1])

    return result


    # args: list[str] = re.split(",|-", arg)
    # if len(args) == 0:
    #     raise ToolError(f"invalid field number arguments: {args}")
    # new_args = []
    # for arg in args:
    #     if "${" in arg or "$(" in arg:
    #         new_args.append(-1)
    #     elif arg == "":
    #         pass
    #     elif not arg.isdigit():
    #         raise ToolError(f"invalid field number: {arg} in {args} in command cut")
    #     else:
    #         new_args.append(int(arg))


    # return new_args