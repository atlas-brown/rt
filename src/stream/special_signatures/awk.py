import re
from stream.command_signature import CommandSignature
from stream.regular_type import RegularType
from stream.tool_error import ToolError
from stream.transducer import compression_FST, cut_field_FST, first_regex_replacement_FST, product_fst_automaton, start_regex_replacement_FST, translate_to_line_delimited_FST, translation_FST
from stream.utils.logger import get_logger

class AwkSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        # Classify the last detailed command invocation as supported
        # get_logger().classify_last_invocation_as_supported()
        
        # Record command pattern based on flag combination
        flag_pattern = get_logger().get_flag_pattern_from_invocation(parsed_command_invocation)
        get_logger().add_command_pattern_log("awk", flag_pattern)
        
        if len(parsed_command_invocation.operand_list) != 1:
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        operand = parsed_command_invocation.operand_list[0].name
        get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = True
        
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
            
        # Check for print statements
        print_match = re.search(r'print\s+([^{}]+)(?=[;}]|$)', operand)
        if not print_match:
            # No print statement, use default behavior
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
            
        print_content = print_match.group(1).strip()
        
        # Check if the print content is just a single variable
        var_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)$', print_content)
        if var_match:
            var_name = var_match.group(1)
            if var_name == "NF":
                # NF is a special variable representing number of fields
                get_logger().get_latest_record()["command_list"][-1]["output_type"] = "[0-9]+"
                return RegularType("[0-9]+")
            elif var_name in int_variables:
                # The variable is an integer, so return a regex pattern for integers
                get_logger().get_latest_record()["command_list"][-1]["output_type"] = "[0-9]+"
                return RegularType("[0-9]+")
        
        # Special handling for print statements with NF and/or column references
        has_nf = re.search(r'\bNF\b', print_content) is not None
        has_column_refs = re.search(r'\$\d+', print_content) is not None
        
        if not has_nf and not has_column_refs:
            # Simple case: regular variables or strings
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
                get_logger().get_latest_record()["command_list"][-1]["output_type"] = "".join(result_parts)
                return RegularType("".join(result_parts))
            
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        
        try:
            # Process a print statement with NF and/or column references
            # First tokenize the print statement to understand what's printed and in what order
            tokens = []
            positions = []
            
            # Find all NF and column references in the print content
            for match in re.finditer(r'(\bNF\b|\$\d+)', print_content):
                token = match.group(1)
                pos = match.span()
                tokens.append(token)
                positions.append(pos)
            
            # Process the tokens into a pattern
            result_type = None
            last_end = 0
            output_type_str = ""
            
            for i, (token, (start, end)) in enumerate(zip(tokens, positions)):
                # Current token's type
                current_type = None
                current_type_str = ""
                
                # Process the token
                if token == "NF":
                    current_type = RegularType("[0-9]+")
                    current_type_str = "[0-9]+"
                elif token.startswith("$"):
                    column_num = int(token[1:])
                    if column_num == 0:
                        # $0 represents the entire input line
                        current_type = previous_output_type
                        current_type_str = "α"
                    else:
                        # We need to extract this column
                        fst0 = translation_FST("\t", " ")
                        fst1 = start_regex_replacement_FST(RegularType(" +").nfa, "")
                        fst2 = compression_FST(" ")
                        fst3 = cut_field_FST(" ", [column_num])
                        nfa = product_fst_automaton(fst0, previous_output_type.nfa)
                        nfa = product_fst_automaton(fst1, nfa)
                        nfa = product_fst_automaton(fst2, nfa)
                        nfa = product_fst_automaton(fst3, nfa)
                        current_type = RegularType(automaton=nfa)
                
                        current_type_str = f'field-select(translate-chars(translate-match(α,"^[ \\t]+", "")," \\t", " ", squeeze=True)," ", {column_num})'
                # Add to result_type
                if current_type:
                    if result_type is None:
                        result_type = current_type
                        output_type_str = current_type_str
                    else:
                        # Concatenate with a space
                        result_type = result_type + RegularType(" ") + current_type
                        output_type_str = output_type_str + " " + current_type_str
                
                last_end = end
            
            get_logger().get_latest_record()["command_list"][-1]["output_type"] = output_type_str
            return result_type if result_type else super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        except Exception:
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        
        