import re
from typing import Optional, Tuple
from stream.command_signature import CommandSignature
from stream.regular_type import RegularType

from stream.tool_error import ToolError

class SortSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations) -> Tuple[RegularType, Optional[RegularType]]:
        input_type, no_input_type = super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)
        flags = set()
        flag_args : dict[str, list[str]] = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, 'get_arg') and flag.get_arg():
                if name not in flag_args:
                    flag_args[name] = []
                flag_args[name].append(flag.get_arg())

        if "-k" not in flags:
            return input_type, no_input_type
        
        input_type = RegularType(".*")
        args = flag_args.get('-k')
        for arg in args:
            flag = ''.join(list(re.finditer(r'[^\d]+$', arg))[0].group()) if re.search(r'[^\d]+$', arg) else ''
            arg = arg.replace(flag, '')
            if "," in arg:
                if flag == "":
                    field, start = arg.split(',')
                    # FIXME: about .
                    try:
                        field, start = int(field), int(start)
                    except Exception as e:
                        return RegularType(".*"), None
                    pattern = f"[\t ]*([^\t ]+[\t ]+){{{field - 1}}}[^\t ]{{{start}}}.*"
                    input_type = input_type & RegularType(pattern)
                else:
                    field, start = arg.split(',')
                    # FIXME: about .
                    try:
                        field, start = int(field), int(start)
                    except Exception as e:
                        return RegularType(".*"), None
                    if "n" in flag:
                        pattern = f"[\t ]*([^\t ]+[\t ]+){{{field - 1}}}[^\t ]{{{start - 1}}}[0-9].*"
                        input_type = input_type & RegularType(pattern)
            else:
                if flag == "":
                    field = int(arg)
                    pattern = f"[\t ]*([^\t ]+[\t ]+){{{field - 1}}}[^\t ]+.*"
                    input_type = input_type & RegularType(pattern)
                else:
                    field = int(arg)
                    if "n" in flag:
                        pattern = f"[\t ]*([^\t ]+[\t ]+){{{field - 1}}}[0-9]+.*"

        return input_type, None
                    

                

                    
                

        

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