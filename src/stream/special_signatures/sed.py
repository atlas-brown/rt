import re
from command_signature import CommandSignature
from stream.regular_type import RegularType
from stream.tool_error import ToolError

class SedSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_input_type(self, parsed_command_invocation, heuristic_rules):
        input_type, no_input_type = super().get_input_type(parsed_command_invocation, heuristic_rules)
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type
        
        operands = super().get_operands(parsed_command_invocation)
        if len(operands) == 0:
            raise ToolError("No operand provided for sed")
        operand = operands[0]
        parts = operand.split("/")
        if len(parts) < 3:
            return input_type, no_input_type
        if parts[0] == 's' and not parts[1].startswith('^') and not parts[1].startswith('$'):
            # FIXME: using re.escape is not totally correct
            # parts[1] = re.escape(parts[1])  
            return input_type, RegularType(f"(?!.*{parts[1]}.*)")
        return input_type, no_input_type


    def output_type_inference(self, previous_output_type, parsed_command_invocation):
        operands = super().get_operands(parsed_command_invocation)
        if len(operands) == 0:
            raise ToolError("No operand provided for sed")
        operand = operands[0]
        if operand == "d":
            return RegularType("")
        if operand[-1] == "d" and operand[:-1].isdigit():
            return RegularType(previous_output_type.pattern)
        parts = operand.split("/")
        if len(parts) < 3:
            return super().output_type_inference(previous_output_type, parsed_command_invocation)
        if parts[0] == 's':
            if parts[1] == '^':
                return RegularType(parts[2] + previous_output_type.pattern)
            elif parts[1] == '$':
                return RegularType(previous_output_type.pattern + parts[2])
            else:
                # FIXME: using re.escape is not totally correct
                parts[1] = re.escape(parts[1])
                return RegularType("(" + previous_output_type.pattern + ")&((?!.*" + parts[1] + ".*))")
            
        return super().output_type_inference(previous_output_type, parsed_command_invocation)
        
