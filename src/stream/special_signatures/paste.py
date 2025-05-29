import re
from stream.command_signature import CommandSignature
from stream.regular_type import RegularType
from stream.tool_error import ToolError
from stream.utils.logger import get_logger

class PasteSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations):
        input_type, no_input_type = super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)
        if len(parsed_command_invocation.operand_list) != 0:
            return RegularType(".*"), None
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type
        
        parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
        if "-s" not in parsed_flags:
            return input_type, RegularType(".*")
        
        return input_type, no_input_type


    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = False
        flags = set()
        flag_args : dict[str, list[str]] = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, 'get_arg') and flag.get_arg():
                if name not in flag_args:
                    flag_args[name] = []
                flag_args[name].append(flag.get_arg())
        if "-s" in flags:
            delimiter = "\t"
            if '-d' in flags:
                delimiter = f"{flag_args['-d']}"

            while (delimiter[0] == "(" and delimiter[-1] == ")") or (delimiter[0] == "[" and delimiter[-1] == "]") or (delimiter[0] == "'" and delimiter[-1] == "'") or (delimiter[0] == '"' and delimiter[-1] == '"'):
                delimiter = delimiter[1:-1]

            delimiter = delimiter[-1] # \" -> "

            get_logger().get_latest_record()["command_list"][-1]["output_type"] = f"α({delimiter}α)*"
            return previous_output_type + (RegularType(f"[{delimiter}]") + previous_output_type).kleene_star()

        
            
        return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        
