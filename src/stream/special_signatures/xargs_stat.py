from command_signature import CommandSignature
from stream.regular_type import RegularType

class XargsStatSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        operands = super().get_operands(parsed_command_invocation)
        for operand, next_operand in zip(operands, operands[1:]):
            if operand == '-c':
                if next_operand == '%Y':
                    # stat -c %Y
                    return RegularType("[0-9]+")
                elif next_operand == '%y':
                    # stat -c %y need to modify the regex
                    return RegularType(".*")
                elif next_operand == '%x':
                    # stat -c %x need to modify the regex
                    return RegularType(".*")
                
        return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        
