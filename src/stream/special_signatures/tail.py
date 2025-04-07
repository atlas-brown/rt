import re
from stream.command_signature import CommandSignature
from stream.regular_type import RegularType
from stream.tool_error import ToolError

class TailSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations):
        input_type, no_input_type = super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)
        if len(parsed_command_invocation.operand_list) > 0:
            return input_type, no_input_type
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type
        flags = set()
        flag_args : dict[str, list[str]] = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, 'get_arg') and flag.get_arg():
                if name not in flag_args:
                    flag_args[name] = []
                flag_args[name].append(flag.get_arg())
        if "-n" in flags:
            num_lines = int(flag_args["-n"][0])
            return input_type, RegularType(".*", possible_line_numbers=(0, num_lines))
        return input_type, no_input_type


    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        if len(parsed_command_invocation.operand_list) > 0:
            previous_output_type = super().get_file_name(parsed_command_invocation, env_annotations)
        flags = set()
        flag_args : dict[str, list[str]] = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, 'get_arg') and flag.get_arg():
                if name not in flag_args:
                    flag_args[name] = []
                flag_args[name].append(flag.get_arg())
        if "-n" in flags:
            num_lines = int(flag_args["-n"][0])
            output_type = previous_output_type
            output_type.possible_line_numbers = (num_lines, num_lines)
            return output_type
        return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        
        
