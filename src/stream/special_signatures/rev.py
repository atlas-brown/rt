import re
from stream.command_signature import CommandSignature, InferenceResult
from stream.regular_type import RegularType, reverse_automaton
from stream.tool_error import ToolError
from stream.utils.logger import get_logger

class RevSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations):
        if len(parsed_command_invocation.operand_list) > 0 and "no_ignored_input" in heuristic_rules:
            return RegularType(""), None
        return super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)


    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = False
        self_contained = True
        if len(parsed_command_invocation.operand_list) > 0:
            previous_output_type = super().get_file_name(parsed_command_invocation, env_annotations)
            get_logger().get_latest_record()["command_list"][-1]["output_type"] = f"reverse({previous_output_type.pattern})"
            if previous_output_type.tainted:
                self_contained = False
        else:
            get_logger().get_latest_record()["command_list"][-1]["output_type"] = "reverse(α)"
        
        return InferenceResult(previous_output_type.reverse(), reverse_automaton, self_contained)
        
