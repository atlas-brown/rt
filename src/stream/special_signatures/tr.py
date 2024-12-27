import re
from command_signature import CommandSignature
from stream.regular_type import RegularType
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from stream.tool_error import ToolError

class TrSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_output_pattern(self, parsed_command_invocation: CommandInvocationInitial) -> str:
        if len(parsed_command_invocation.operand_list) == 0:
            raise ToolError("No pattern provided for tr")
        parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
        if len(parsed_command_invocation.operand_list) == 0:
            raise ToolError("No pattern provided for tr")
        set1 = parsed_command_invocation.operand_list[0].name

        if set1.startswith("[") and set1.endswith("]"):
            set1 = set1[1:-1]

        if "-c" in parsed_flags:
            return f".*[{set1}]+.*"
        
        if "-s" in parsed_flags:
            pattern = ""
            for i, c in enumerate(set1):
                c = re.escape(c)
                pattern = pattern + c + c
                if i < len(set1) - 1:
                    pattern += "|"
            return f"(?!.*({pattern}).*)"
    
        return f"(?!.*[{set1}].*)"
        

    def get_input_type(self, parsed_command_invocation, heuristic_rules):
        input_type, no_input_type = super().get_input_type(parsed_command_invocation, heuristic_rules)
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type
        return input_type, RegularType(self.get_output_pattern(parsed_command_invocation))

    def output_type_inference(self, previous_output_type, parsed_command_invocation):
        return RegularType(f"({previous_output_type.pattern}&{self.get_output_pattern(parsed_command_invocation)})")