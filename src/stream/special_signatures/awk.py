import re
from stream.command_signature import CommandSignature
from stream.command_type import PolymorphicCommandType
from stream.regular_type import RegularType
from stream.transformation_ast import (
    ALPHA,
    ConcatenateTransform,
    ComposeTransform,
    ConstantTransform,
    FieldSelectTransform,
    LastFieldTransform,
    TranslateCharsTransform,
    TranslateMatchTransform,
)
from stream.tool_error import ToolError

class AwkSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def construct_command_type(self, parsed_command_invocation, env_annotations):
        operand = self._get_awk_program(parsed_command_invocation)
        if operand is None:
            return super().construct_command_type(parsed_command_invocation, env_annotations)
        if "\\s" in operand:
            raise ToolError("awk regular expressions do not support the '\\s' character class in POSIX awk")

        normalized_operand = re.sub(r'\$\{(NF|\d+)\}', lambda match: f'${match.group(1)}', operand)
        field_separator = self._get_field_separator(parsed_command_invocation)
        operands = [operand.name for operand in parsed_command_invocation.operand_list]
        program_index = self._get_program_operand_index(parsed_command_invocation)
        source = ALPHA
        self_contained = True
        if program_index is not None and program_index + 1 < len(operands):
            file_type = super().get_file_name(parsed_command_invocation, env_annotations)
            if file_type.tainted:
                self_contained = False
            source = ConstantTransform(file_type)

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

        print_match = re.search(r'print\s+([^{}]+)(?=[;}]|$)', normalized_operand)
        if not print_match:
            return super().construct_command_type(parsed_command_invocation, env_annotations)
        print_content = print_match.group(1).strip()

        if re.search(r'\$(?!NF\b)[a-zA-Z_][a-zA-Z0-9_]*|\$\{[a-zA-Z_][a-zA-Z0-9_]*\}', print_content):
            return super().construct_command_type(parsed_command_invocation, env_annotations)

        var_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)$', print_content)
        if var_match:
            var_name = var_match.group(1)
            if var_name == "NF" or var_name in int_variables:
                return PolymorphicCommandType(ConstantTransform(RegularType("[0-9]+")), self_contained=True)
            return super().construct_command_type(parsed_command_invocation, env_annotations)

        has_nf = re.search(r'\bNF\b', print_content) is not None
        has_column_refs = re.search(r'\$\d+', print_content) is not None

        if not has_nf and not has_column_refs:
            result_parts = []
            for part in re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*|"[^"]*")', print_content):
                if part.startswith('"') and part.endswith('"'):
                    result_parts.append(re.escape(part[1:-1]))
                elif part in int_variables:
                    result_parts.append("[0-9]+")
                else:
                    result_parts.append(".*")
            if result_parts:
                return PolymorphicCommandType(ConstantTransform(RegularType("".join(result_parts))), self_contained=True)
            return super().construct_command_type(parsed_command_invocation, env_annotations)

        try:
            result_transform = None
            for token in re.findall(r'(\$NF|\bNF\b|\$\d+)', print_content):
                if token == "NF":
                    current_transform = ConstantTransform(RegularType("[0-9]+"))
                elif token == "$NF":
                    current_transform = ComposeTransform(
                        LastFieldTransform(ALPHA, field_separator),
                        source,
                    )
                elif token.startswith("$"):
                    column_num = int(token[1:])
                    if column_num == 0:
                        current_transform = source
                    elif field_separator == " ":
                        normalized_source = self._default_field_separator_transform(source)
                        current_transform = ComposeTransform(
                            FieldSelectTransform(ALPHA, " ", str(column_num)),
                            normalized_source,
                        )
                    elif len(field_separator) == 1:
                        current_transform = ComposeTransform(
                            FieldSelectTransform(ALPHA, field_separator, str(column_num)),
                            source,
                        )
                    else:
                        return super().construct_command_type(parsed_command_invocation, env_annotations)
                else:
                    continue

                if result_transform is None:
                    result_transform = current_transform
                else:
                    result_transform = ConcatenateTransform(
                        ConcatenateTransform(result_transform, ConstantTransform(RegularType(" ", tainted=False))),
                        current_transform,
                    )

            if result_transform is not None:
                return PolymorphicCommandType(result_transform, self_contained=self_contained)
            return super().construct_command_type(parsed_command_invocation, env_annotations)
        except Exception:
            return super().construct_command_type(parsed_command_invocation, env_annotations)

    @staticmethod
    def _default_field_separator_transform(source):
        tab_to_space = ComposeTransform(
            TranslateCharsTransform(ALPHA, "\t", " "),
            source,
        )
        trim_leading_spaces = ComposeTransform(
            TranslateMatchTransform(ALPHA, "^ +", ""),
            tab_to_space,
        )
        return ComposeTransform(
            TranslateCharsTransform(ALPHA, " ", " ", squeeze=True),
            trim_leading_spaces,
        )

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
