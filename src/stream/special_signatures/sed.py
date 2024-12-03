from command_signature import CommandSignature
from stream.regular_type import RegularType

class SedSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def output_type_inference(self, previous_output_type, parsed_command_invocation):
        operands = super().get_operands(parsed_command_invocation)
        operand = operands[0]
        parts = operand.split(";")
        if parts[0] == 's':
            if parts[1] == '^':
                return RegularType(parts[2] + previous_output_type.pattern)
            elif parts[1] == '$':
                return RegularType(previous_output_type.pattern + parts[2])
            else:
                return RegularType("{" + previous_output_type.pattern + "}&{(?!" + parts[2] + ")}")
            
        return super().output_type_inference(previous_output_type, parsed_command_invocation)
        
