import re
from typing import Optional, Tuple
from stream.command_signature import CommandSignature
from stream.command_type import PolymorphicCommandType, NoInputReason
from stream.regular_type import RegularType
from stream.transformation_ast import ALPHA, ConstantTransform, FieldSelectTransform

from stream.tool_error import ToolError


class CutSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations) -> Tuple[RegularType, Optional[RegularType], Optional[NoInputReason]]:
        if len(parsed_command_invocation.operand_list) > 0 and "no_ignored_input" in heuristic_rules:
            return RegularType(""), None, None
        
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
                return RegularType(".*"), None, None
            if field_num < 1:
                raise ToolError(f"field number must be greater than 0: {field_num}")
            if field_num == 1:
                if "no_meaningless_command" not in heuristic_rules:
                    return RegularType(".*"), None, None
                else:
                    no_input_type = RegularType("[^" + delimiter + "]*")
                    no_input_type.tainted = False
                    return RegularType(".*"), no_input_type, NoInputReason.FILTER
            
            pattern = f"[^{delimiter}]*({re.escape(delimiter)}[^{delimiter}]*){{0,{field_num-2}}}"
            if "no_meaningless_command" not in heuristic_rules:
                return RegularType(".*"), None, None
            else:
                no_input_type = RegularType(pattern)
                no_input_type.tainted = False
                return RegularType(".*"), no_input_type, NoInputReason.FILTER
            
        return super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)

    def construct_command_type(self, parsed_command_invocation, env_annotations):
        source = ALPHA
        self_contained = True
        if len(parsed_command_invocation.operand_list) > 0:
            file_name = parsed_command_invocation.operand_list[0].name
            annotated = self._annotated_content_type(file_name, env_annotations)
            if annotated is None:
                annotated = RegularType(".*")
                self_contained = False
            source = ConstantTransform(annotated)

        flags = set()
        flag_args = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, "get_arg") and flag.get_arg():
                flag_args[name] = flag.get_arg()

        try:
            if flags == {"-b"} or flags == {"-c"}:
                flag_arg = flag_args.get("-c") if "-c" in flags else flag_args.get("-b")
                transform = FieldSelectTransform(source, "", flag_arg)
            elif flags == {"-f"} or flags == {"-d", "-f"}:
                flag_arg = flag_args.get("-f")
                delimiter = "\t"
                if "-d" in flags:
                    delimiter = f"{flag_args['-d']}"
                transform = FieldSelectTransform(source, delimiter, flag_arg)
            else:
                transform = ConstantTransform(RegularType(".*"))
        except Exception:
            transform = ConstantTransform(RegularType(".*"))

        return PolymorphicCommandType(transform, self_contained=self_contained)

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
