from command_signature import CommandSignature
from stream.regular_type import RegularType

class SedSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def inference_output_type(self, previous_output_type, parsed_command_node):
        operands = super().get_operands(parsed_command_node)
        operand = operands[0]
        parts = operand.split(";")
        if parts[0] == 's':
            if parts[1] == '^':
                return RegularType(parts[2] + previous_output_type.pattern)
            elif parts[1] == '$':
                return RegularType(previous_output_type.pattern + parts[2])
            else:
                return RegularType("{" + previous_output_type.pattern + "}&{(?!" + parts[2] + ")}")
            
        return super().inference_output_type(previous_output_type, parsed_command_node)
        
