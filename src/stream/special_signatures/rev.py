import re
from stream.command_signature import CommandSignature
from stream.regular_type import RegularType
from stream.tool_error import ToolError

class RevSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations):
        if len(parsed_command_invocation.operand_list) > 0 and "no_ignored_input" in heuristic_rules:
            return RegularType(""), None
        return super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)


    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        if len(parsed_command_invocation.operand_list) > 0:
            previous_output_type = super().get_file_name(parsed_command_invocation, env_annotations)
        return previous_output_type.reverse()
        
