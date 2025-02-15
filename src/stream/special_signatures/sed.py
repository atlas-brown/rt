import re
from command_signature import CommandSignature
from stream.regular_type import RegularType, concat
from stream.tool_error import ToolError
from stream.regular_type import intersect, complement

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
            parts[1] = parts[1].replace("\\\\", "\\")
            # FIXME: provisional solution for sed s/\///g : if ends with an odd number of backslashes, then add '/' to the end
            match = re.search(r'(\\+)$', parts[1])
            if match and (len(match.group(1)) % 2 == 1):
                parts[1] = parts[1] + '/'
            return input_type, complement(concat([RegularType(".*"), RegularType(parts[1]), RegularType(".*")]))
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
                parts[2] = parts[2].replace("\\\\", "\\")
                return concat([RegularType(parts[2]), previous_output_type])
            elif parts[1] == '$':
                parts[2] = parts[2].replace("\\\\", "\\")
                return concat([previous_output_type, RegularType(parts[2])])
            else:
                parts[1] = parts[1].replace("\\\\", "\\")
                # FIXME: provisional solution for sed s/\///g : if ends with an odd number of backslashes, then add '/' to the end
                match = re.search(r'(\\+)$', parts[1])
                if match and (len(match.group(1)) % 2 == 1):
                    parts[1] = parts[1] + '/'
                
                return intersect(previous_output_type, complement(concat([RegularType(".*"), RegularType(parts[1]), RegularType(".*")])))
            
        return super().output_type_inference(previous_output_type, parsed_command_invocation)
        
