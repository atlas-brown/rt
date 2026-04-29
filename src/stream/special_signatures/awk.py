import re
from stream.command_signature import CommandSignature, InferenceResult
from stream.regular_type import RegularType
from stream.tool_error import ToolError
from stream.transducer import compression_FST, cut_field_FST, first_regex_replacement_FST, product_fst_automaton, start_regex_replacement_FST, translate_to_line_delimited_FST, translation_FST

class AwkSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_previous_output_type = None

    def determine_output_type(self, previous_output_type, parsed_command_invocation, user_annotations, env_annotations):
        self._original_previous_output_type = previous_output_type
        try:
            return super().determine_output_type(
                previous_output_type,
                parsed_command_invocation,
                user_annotations,
                env_annotations,
            )
        finally:
            self._original_previous_output_type = None

    @staticmethod
    def _get_program_operand_index(parsed_command_invocation):
        operands = [operand.name for operand in parsed_command_invocation.operand_list]
        parsed_flags = {flag.get_name() for flag in parsed_command_invocation.flag_option_list}

        if "-F" in parsed_flags and len(operands) >= 2:
            return 1

        index = 0

        while index < len(operands):
            operand = operands[index]
            if operand == "--":
                index += 1
                break
            if operand in {"-F", "-f", "-v"}:
                index += 2
                continue
            if operand.startswith("-F") and operand != "-F":
                index += 1
                continue
            if operand.startswith("-f") and operand != "-f":
                index += 1
                continue
            if operand.startswith("-v") and operand != "-v":
                index += 1
                continue
            if operand.startswith("-"):
                index += 1
                continue
            break

        return index if index < len(operands) else None

    @classmethod
    def _get_awk_program(cls, parsed_command_invocation):
        operands = [operand.name for operand in parsed_command_invocation.operand_list]
        program_index = cls._get_program_operand_index(parsed_command_invocation)
        return operands[program_index] if program_index is not None else None

    @staticmethod
    def _get_field_separator(parsed_command_invocation) -> str:
        operands = [operand.name for operand in parsed_command_invocation.operand_list]
        parsed_flags = {flag.get_name() for flag in parsed_command_invocation.flag_option_list}

        if "-F" in parsed_flags and operands:
            delimiter = operands[0]
        else:
            delimiter = " "

            for index, operand in enumerate(operands):
                if operand == "-F" and index + 1 < len(operands):
                    delimiter = operands[index + 1]
                    break
                if operand.startswith("-F") and operand != "-F":
                    delimiter = operand[2:]
                    break

        while len(delimiter) >= 2 and (
            (delimiter[0] == "(" and delimiter[-1] == ")")
            or (delimiter[0] == "[" and delimiter[-1] == "]")
            or (delimiter[0] == "'" and delimiter[-1] == "'")
            or (delimiter[0] == '"' and delimiter[-1] == '"')
        ):
            delimiter = delimiter[1:-1]

        if delimiter.startswith("\\") and len(delimiter) == 2:
            delimiter = delimiter[1]

        return delimiter

    @staticmethod
    def _infer_last_field_type(previous_output_type, delimiter: str):
        if (
            previous_output_type.pattern
            and delimiter
            and delimiter in previous_output_type.pattern
            and len(delimiter) == 1
            and delimiter not in {".", "[", "]", "(", ")", "{", "}", "*", "+", "?", "|", "^", "$", "\\"}
        ):
            suffix = previous_output_type.pattern.rsplit(delimiter, 1)[1]
            if suffix:
                return RegularType(suffix, repr_mode=previous_output_type.repr_mode, tainted=previous_output_type.tainted)

        if delimiter:
            fst = start_regex_replacement_FST(RegularType(f".*{re.escape(delimiter)}").nfa, "")
            return RegularType(
                automaton=product_fst_automaton(fst, previous_output_type.nfa),
                tainted=previous_output_type.tainted,
            )

        return previous_output_type

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        
        operand = self._get_awk_program(parsed_command_invocation)
        if operand is None:
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        if "\\s" in operand:
            raise ToolError("awk regular expressions do not support the '\\s' character class in POSIX awk")
        normalized_operand = re.sub(r'\$\{(NF|\d+)\}', lambda match: f'${match.group(1)}', operand)
        field_separator = self._get_field_separator(parsed_command_invocation)
        operands = [operand.name for operand in parsed_command_invocation.operand_list]
        program_index = self._get_program_operand_index(parsed_command_invocation)
        if program_index is not None and program_index + 1 < len(operands):
            previous_output_type = super().get_file_name(parsed_command_invocation, env_annotations)
        
        # First, identify variables used in increment/decrement operations (i++, ++i, i--, --i)
        # These variables can be inferred to be integers
        int_variables = set()
        for var in re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\+\+', normalized_operand):
            int_variables.add(var)
        for var in re.findall(r'\+\+([a-zA-Z_][a-zA-Z0-9_]*)', normalized_operand):
            int_variables.add(var)
        for var in re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)--', normalized_operand):
            int_variables.add(var)
        for var in re.findall(r'--([a-zA-Z_][a-zA-Z0-9_]*)', normalized_operand):
            int_variables.add(var)
        for var in re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\+|-|\*|/)?=\s*(?:NF|\$\d+|[0-9]+)', normalized_operand):
            int_variables.add(var)
            
        # Check for print statements
        print_match = re.search(r'print\s+([^{}]+)(?=[;}]|$)', normalized_operand)
        if not print_match:
            # No print statement, use default behavior
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
            
        print_content = print_match.group(1).strip()

        # Dynamic field references such as $i are not modeled precisely.
        # Fall back to the generic command signature instead of treating the
        # loop/index variable as the printed value.
        if re.search(r'\$(?!NF\b)[a-zA-Z_][a-zA-Z0-9_]*|\$\{[a-zA-Z_][a-zA-Z0-9_]*\}', print_content):
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        
        # Check if the print content is just a single variable
        var_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)$', print_content)
        if var_match:
            var_name = var_match.group(1)
            if var_name == "NF" or var_name in int_variables:
                return InferenceResult(RegularType("[0-9]+"), None, True)
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        
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
                return InferenceResult(RegularType("".join(result_parts)), None, True)
            
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        
        try:
            # Process a print statement with NF and/or column references
            # First tokenize the print statement to understand what's printed and in what order
            tokens = []
            positions = []
            
            # Find all NF and column references in the print content
            for match in re.finditer(r'(\$NF|\bNF\b|\$\d+)', print_content):
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
                elif token == "$NF":
                    source_output_type = previous_output_type
                    if (
                        not (program_index is not None and program_index + 1 < len(operands))
                        and (
                        previous_output_type.pattern is None
                        and self._original_previous_output_type is not None
                        and self._original_previous_output_type.pattern is not None
                        )
                    ):
                        source_output_type = self._original_previous_output_type
                    current_type = self._infer_last_field_type(source_output_type, field_separator)
                    current_type_str = f"last-field(α, {re.escape(field_separator)})"
                elif token.startswith("$"):
                    column_num = int(token[1:])
                    if column_num == 0:
                        # $0 represents the entire input line
                        current_type = previous_output_type
                        current_type_str = "α"
                    else:
                        # We need to extract this column.
                        if field_separator == " ":
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
                        elif len(field_separator) == 1:
                            fst = cut_field_FST(field_separator, [column_num])
                            current_type = RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa))
                            current_type_str = f'field-select(α, {re.escape(field_separator)}, {column_num})'
                        else:
                            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
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
            
            return InferenceResult(result_type, None, True) if result_type else super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        except Exception:
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        
        
