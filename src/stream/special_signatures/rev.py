import re
from command_signature import CommandSignature
from stream.regular_type import RegularType
from stream.tool_error import ToolError

class RevSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def output_type_inference(self, previous_output_type, parsed_command_invocation):
        return previous_output_type.reverse()
        
