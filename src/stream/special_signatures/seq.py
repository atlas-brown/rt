from command_signature import CommandSignature
from stream.regular_type import RegularType
from stream.tool_error import ToolError

class SeqSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        operands = super().get_operands(parsed_command_invocation)
        if len(operands) == 0:
            raise ToolError("No operand provided for seq")
        if len(operands) == 1 and operands[0].isdigit():
            if int(operands[0]) <= 0:
                return RegularType("")
            else:
                return RegularType("[0-9]+")
        if len(operands) == 2 and operands[0].isdigit():
            if int(operands[0]) < 0:
                return RegularType("-?[0-9]+")
            else:
                return RegularType("[0-9]+")
        
        return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        
