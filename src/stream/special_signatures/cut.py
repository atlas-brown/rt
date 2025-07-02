import re
from typing import Optional, Tuple
from stream.command_signature import CommandSignature, InferenceResult
from stream.regex_parser import convert_to_pure_string
from stream.regular_type import RegularType
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from stream.tool_error import ToolError
from stream.transducer import correct_cut_field_FST, cut_char_FST, cut_field_FST, line_based_functional_to_stream_FST, product_fst_automaton
from stream.user_annotation import AnnotationType
from stream.utils.logger import get_logger


# FIXME: if the delimiter does not appear in the input, the output should be the same as the input
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
                    no_input_type = RegularType("[^" + delimiter + "]*")
                    no_input_type.tainted = False
                    return RegularType(".*"), no_input_type
            
            pattern = f"[^{delimiter}]*({re.escape(delimiter)}[^{delimiter}]*){{0,{field_num-2}}}"
            if "no_meaningless_command" not in heuristic_rules:
                return RegularType(".*"), None
            else:
                no_input_type = RegularType(pattern)
                no_input_type.tainted = False
                return RegularType(".*"), no_input_type
            
        return super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)

    def output_type_inference(self, previous_output_type: RegularType, parsed_command_invocation: CommandInvocationInitial, env_annotations) -> RegularType:
        # Classify the last detailed command invocation as supported
        # get_logger().classify_last_invocation_as_supported()
        supported_flags = set(["-b", "-c", "-d", "-f", "--complement"])
        
        # Record command pattern based on flag combination
        flag_pattern = get_logger().get_flag_pattern_from_invocation(parsed_command_invocation)
        get_logger().add_command_pattern_log("cut", flag_pattern)
        
        get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = False
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

        if flags.issubset(supported_flags):
            get_logger().classify_last_invocation_as_supported()
        else:
            get_logger().classify_last_invocation_as_unsupported()

        if flags == {"-b"} or flags == {"-c"}:
            flag_arg = flag_args.get('-c') if "-c" in flags else flag_args.get('-b')
            args, has_upperbound = preprocess(flag_arg)
            if len(args) == 0:
                get_logger().get_latest_record()["command_list"][-1]["output_type"] = ".*"
                return InferenceResult(RegularType(".*"), None, True)
            fst = cut_char_FST(args, has_upperbound)
            if previous_output_type.repr_mode == "stream":
                fst = line_based_functional_to_stream_FST(fst)
            get_logger().get_latest_record()["command_list"][-1]["output_type"] = f"field-select(α, {flag_arg}, \"\")"
            output_type = RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa), tainted=previous_output_type.tainted, repr_mode=previous_output_type.repr_mode)
            return InferenceResult(output_type, None, True)
        if flags == {"-f"} or flags == {"-d", "-f"}:
            flag_arg = flag_args.get('-f') if "-f" in flags else flag_args.get('-d')
            args, has_upperbound = preprocess(flag_arg)
            delimiter = "\t"
            if '-d' in flags:
                delimiter = f"{flag_args['-d']}"
            while (delimiter[0] == "(" and delimiter[-1] == ")") or (delimiter[0] == "[" and delimiter[-1] == "]") or (delimiter[0] == "'" and delimiter[-1] == "'") or (delimiter[0] == '"' and delimiter[-1] == '"'):
                delimiter = delimiter[1:-1]
            delimiter = delimiter[-1] # \" -> "
            if len(args) == 0:
                get_logger().get_latest_record()["command_list"][-1]["output_type"] = ".*"
                return InferenceResult(RegularType(".*"), None, True)
            fst = correct_cut_field_FST(delimiter, args, has_upperbound)
            if previous_output_type.repr_mode == "stream":
                fst = line_based_functional_to_stream_FST(fst)
            get_logger().get_latest_record()["command_list"][-1]["output_type"] = f"field-select(α&.*[{delimiter}].*, {flag_arg}, {delimiter})|α&[^{delimiter}]*"
            output_type = RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa), tainted=previous_output_type.tainted, repr_mode=previous_output_type.repr_mode)
            return InferenceResult(output_type, None, True)
        
        get_logger().get_latest_record()["command_list"][-1]["output_type"] = ".*"
        return InferenceResult(RegularType(".*"), None, True)



        if "-b" in flags or "-c" in flags:
            args1 = preprocess(flag_args.get('-c'))
            args2 = preprocess(flag_args.get('-b'))
            flag_arg = flag_args.get('-c') if "-c" in flags else flag_args.get('-b')
            args = args1 + args2
            if len(args) == 0:
                get_logger().get_latest_record()["command_list"][-1]["output_type"] = ".*"
                return RegularType(".*")
            if args[-1] == -1:
                if len(args) == 2:
                    get_logger().get_latest_record()["command_list"][-1]["output_type"] = f"field-select(α, {flag_arg}, \"\")"
                    fst = cut_char_no_upperbound_FST(args[-2])
                    return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa), tainted=previous_output_type.tainted)
                fst1 = cut_char_FST(args[:-2])
                fst2 = cut_char_no_upperbound_FST(args[-2])
                get_logger().get_latest_record()["command_list"][-1]["output_type"] = f"field-select(α, {flag_arg}, \"\")"
                return RegularType(automaton=product_fst_automaton(fst1, previous_output_type.nfa), tainted=previous_output_type.tainted) + RegularType(automaton=product_fst_automaton(fst2, previous_output_type.nfa), tainted=previous_output_type.tainted)
            fst = cut_char_FST(args)
            get_logger().get_latest_record()["command_list"][-1]["output_type"] = f"field-select(α, {flag_arg}, \"\")"
            return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa), tainted=previous_output_type.tainted)

        delimiter = "\t"
        if '-d' in flags:
            delimiter = f"{flag_args['-d']}"

        while (delimiter[0] == "(" and delimiter[-1] == ")") or (delimiter[0] == "[" and delimiter[-1] == "]") or (delimiter[0] == "'" and delimiter[-1] == "'") or (delimiter[0] == '"' and delimiter[-1] == '"'):
            delimiter = delimiter[1:-1]
        delimiter = delimiter[-1] # \" -> "

        if '-f' in flags:
            args = preprocess(flag_args.get('-f'))
            if len(args) == 0:
                get_logger().get_latest_record()["command_list"][-1]["output_type"] = ".*"
                return RegularType(".*")
            if args[-1] == -1:
                if len(args) == 2:
                    fst = cut_field_no_upperbound_FST(delimiter, args[-2])
                    get_logger().get_latest_record()["command_list"][-1]["output_type"] = f"field-select(α&.*[{delimiter}].*, {flag_args.get('-f')}, {delimiter})|α&[^{delimiter}]*"
                    return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa), tainted=previous_output_type.tainted)
                fst1 = cut_field_FST(delimiter, args[:-2])
                fst2 = cut_field_no_upperbound_FST(delimiter, args[-2], leading_delimiter=True)
                get_logger().get_latest_record()["command_list"][-1]["output_type"] = f"field-select(α&.*[{delimiter}].*, {flag_args.get('-f')}, {delimiter})|α&[^{delimiter}]*"
                return RegularType(automaton=product_fst_automaton(fst1, previous_output_type.nfa), tainted=previous_output_type.tainted) + RegularType(automaton=product_fst_automaton(fst2, previous_output_type.nfa), tainted=previous_output_type.tainted)
            fst = cut_field_FST(delimiter, args)
            get_logger().get_latest_record()["command_list"][-1]["output_type"] = f"field-select(α&.*[{delimiter}].*, {flag_args.get('-f')}, {delimiter})|α&[^{delimiter}]*"
            return RegularType(automaton=product_fst_automaton(fst, (previous_output_type & RegularType(".*[" + delimiter + "].*")).nfa), tainted=previous_output_type.tainted) | (previous_output_type - RegularType(".*[" + delimiter + "].*", tainted=previous_output_type.tainted))

        
        return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        # if '-f' in flags:
        #     field_num = int(flag_args.get('-f', '1'))
        #     pattern = previous_output_type.pattern
            
        #     field_patterns = re.split(delimiter, pattern)
        #     if field_num <= len(field_patterns):
        #         return RegularType(field_patterns[field_num - 1])
        #     raise ValueError(f"when cutting by field number, the field number must be less than or equal to the number of fields in the input: {field_num} > {len(field_patterns)}")
            
        # return super().inference_output_type(previous_output_type, parsed_command_node)

def preprocess(arg: str) -> Tuple[list[int], bool]: # return value: fields, has_upperbound
    # 1- -> [1], False
    # -2 -> [1, 2], True
    # 1-3 -> [1, 2, 3], True
    # 1, 3 -> [1, 3], True
    if not arg:
        return [], False
    
    if "${" in arg or "$(" in arg:
        return [], False
        
    result = []
    parts = arg.split(',')
    has_upperbound = True
    no_upperbound_start = float('inf')
        
    for part in parts:
        if "-" in part:
            range_parts = part.split('-')
            if len(range_parts) != 2:
                raise ToolError(f"invalid range format: {part}")
                
            start, end = range_parts
            if not start:
                start = 1
            if not end:
                has_upperbound = False
                end = -1
                
            try:
                start, end = int(start), int(end)
                if end == -1:
                    no_upperbound_start = int(min(start, no_upperbound_start))
                else:
                    result.extend(range(start, end + 1))
            except ValueError:
                raise ToolError(f"invalid range values: {part}")
                
        else:
            try:
                result.append(int(part))
            except ValueError:
                raise ToolError(f"invalid field number: {part}")
    if not has_upperbound:
        result = [x for x in result if x < no_upperbound_start]
        result.append(no_upperbound_start)

    return result, has_upperbound


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