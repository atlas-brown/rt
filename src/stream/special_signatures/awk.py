import re
from stream.command_signature import CommandSignature
from stream.regular_type import RegularType
from stream.tool_error import ToolError
from stream.transducer import compression_FST, cut_field_FST, first_regex_replacement_FST, product_fst_automaton, translate_to_line_delimited_FST

class AwkSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        if len(parsed_command_invocation.operand_list) != 1:
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        operand = parsed_command_invocation.operand_list[0].name
        
        # First, identify variables used in increment/decrement operations (i++, ++i, i--, --i)
        # These variables can be inferred to be integers
        int_variables = set()
        for var in re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\+\+', operand):
            int_variables.add(var)
        for var in re.findall(r'\+\+([a-zA-Z_][a-zA-Z0-9_]*)', operand):
            int_variables.add(var)
        for var in re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)--', operand):
            int_variables.add(var)
        for var in re.findall(r'--([a-zA-Z_][a-zA-Z0-9_]*)', operand):
            int_variables.add(var)
            
        # Check for print statements with variables
        print_match = re.search(r'print\s+([^${}]+)(?=[;}]|$)', operand)
        if print_match and not re.search(r'\$\d+', print_match.group(1)):
            # Print statement with potential variables but no $n references
            print_content = print_match.group(1).strip()
            
            # Check if the print content is just a variable that's been identified as an integer
            var_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)$', print_content)
            if var_match and var_match.group(1) in int_variables:
                # The variable is an integer, so return a regex pattern for integers
                return RegularType("[0-9]+")
                
            # Check for concatenated variables/strings and process accordingly
            result_parts = []
            for part in re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*|"[^"]*")', print_content):
                if part.startswith('"') and part.endswith('"'):
                    # String literal
                    result_parts.append(re.escape(part[1:-1]))
                elif part in int_variables:
                    # Integer variable
                    result_parts.append("[0-9]+")
                else:
                    # Unknown variable, assume any character
                    result_parts.append(".*")
            
            if result_parts:
                return RegularType("".join(result_parts))
        
        # Extract all column references ($0, $1, $2, etc.) from the awk command
        matches = re.findall(r'\$(\d+)', operand)
        if not matches:
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        
        try:
            # Convert all column numbers to integers
            column_numbers = [int(match) for match in matches]
            
            # Handle print statements with multiple columns
            if 'print' in operand:
                # Special handling for $0 which represents the entire input line
                if 0 in column_numbers:
                    # Split columns into groups: before $0, $0, and after $0
                    zero_index = column_numbers.index(0)
                    before_zero = column_numbers[:zero_index]
                    after_zero = column_numbers[zero_index+1:]
                    
                    result_type = None
                    
                    # Process columns before $0
                    if before_zero:
                        fst1 = first_regex_replacement_FST(RegularType(" +").nfa, "")
                        fst2 = compression_FST(" ")
                        fst3 = cut_field_FST(" ", before_zero)
                        nfa = product_fst_automaton(fst1, previous_output_type.nfa)
                        nfa = product_fst_automaton(fst2, nfa)
                        nfa = product_fst_automaton(fst3, nfa)
                        result_type = RegularType(automaton=nfa)
                    
                    # Add $0 (entire input line)
                    if result_type:
                        # Add space and then input type
                        result_type = RegularType(result_type.pattern + " " + previous_output_type.pattern)
                    else:
                        result_type = previous_output_type
                    
                    # Process columns after $0
                    if after_zero:
                        fst1 = first_regex_replacement_FST(RegularType(" +").nfa, "")
                        fst2 = compression_FST(" ")
                        fst3 = cut_field_FST(" ", after_zero)
                        nfa = product_fst_automaton(fst1, previous_output_type.nfa)
                        nfa = product_fst_automaton(fst2, nfa)
                        nfa = product_fst_automaton(fst3, nfa)
                        after_type = RegularType(automaton=nfa)
                        
                        # Add space and then after columns
                        result_type = RegularType(result_type.pattern + " " + after_type.pattern)
                    
                    return result_type
                else:
                    # Normal processing without $0
                    fst1 = first_regex_replacement_FST(RegularType(" +").nfa, "")
                    fst2 = compression_FST(" ")
                    fst3 = cut_field_FST(" ", column_numbers)
                    nfa = product_fst_automaton(fst1, previous_output_type.nfa)
                    nfa = product_fst_automaton(fst2, nfa)
                    nfa = product_fst_automaton(fst3, nfa)
                    return RegularType(automaton=nfa)
            
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        except Exception:
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        
        