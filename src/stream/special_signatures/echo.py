import re
from stream.command_signature import CommandSignature
from stream.regular_type import RegularType
from stream.tool_error import ToolError
from stream.utils.logger import get_logger

class EchoSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = False
        operands = super().get_operands(parsed_command_invocation)
        if len(operands) == 0:
            raise ToolError("No operand provided for echo")        
        flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
        pattern = re.escape(operands[0])
        if "-n" not in flags:
            pattern = pattern + "\n"
        get_logger().get_latest_record()["command_list"][-1]["output_type"] = pattern
        return RegularType(pattern, repr_mode="stream", tainted=False)
        
