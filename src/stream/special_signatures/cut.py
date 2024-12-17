import re
from typing import Optional, Tuple
from command_signature import CommandSignature
from stream.regular_type import RegularType
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from stream.tool_error import ToolError

class CutSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_input_type(self, parsed_command_invocation, heuristic_rules) -> Tuple[RegularType, Optional[RegularType]]:
        flags = set()
        flag_args = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, 'get_arg') and flag.get_arg():
                flag_args[name] = flag.get_arg()

        delimiter = r"(\t+)"
        if '-d' in flags:
            flag_args['-d'] = re.escape(flag_args['-d'])
            delimiter = f"({flag_args['-d']}+)"

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
                return RegularType(".*")
            if field_num < 1:
                raise ToolError(f"field number must be greater than 0: {field_num}")
            if field_num == 1:
                return RegularType(".*")
            
            pattern = f".*({delimiter}.*){{{field_num-1}}}"
            return RegularType(pattern), None
            
        return super().get_input_type(parsed_command_invocation)

    def output_type_inference(self, previous_output_type: RegularType, parsed_command_invocation: CommandInvocationInitial) -> RegularType:
        return super().output_type_inference(previous_output_type, parsed_command_invocation)
        # if '-f' in flags:
        #     field_num = int(flag_args.get('-f', '1'))
        #     pattern = previous_output_type.pattern
            
        #     field_patterns = re.split(delimiter, pattern)
        #     if field_num <= len(field_patterns):
        #         return RegularType(field_patterns[field_num - 1])
        #     raise ValueError(f"when cutting by field number, the field number must be less than or equal to the number of fields in the input: {field_num} > {len(field_patterns)}")
            
        # return super().inference_output_type(previous_output_type, parsed_command_node)