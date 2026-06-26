import re
from stream.command_signature import CommandSignature
from stream.command_type import PolymorphicCommandType
from stream.regular_type import RegularType
from stream.transformation_ast import ConstantTransform
from stream.tool_error import ToolError
from stream.user_annotation import AnnotationType

class EchoSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def _variable_pattern(token: str, env_annotations) -> str:
        candidate_keys = [token]
        if token.startswith("${") and token.endswith("}"):
            candidate_keys.append(f"${token[2:-1]}")
        elif token.startswith("$") and len(token) > 1:
            candidate_keys.append("${" + token[1:] + "}")

        for key in candidate_keys:
            for annot in env_annotations.get(key, []):
                if annot.annotation_type == AnnotationType.VAR:
                    return annot.pattern
        return "[^\n]*"

    def construct_command_type(self, parsed_command_invocation, env_annotations):
        self_contained = True
        operands = super().get_operands(parsed_command_invocation)
        if len(operands) == 0:
            raise ToolError("No operand provided for echo")

        original_operand = operands[0]
        var_matches = list(re.finditer(r"(\$\{.*?\}|\$[a-zA-Z_][a-zA-Z0-9_]*)", original_operand))
        if not var_matches:
            pattern = re.escape(original_operand)
        else:
            pattern_parts = []
            last_end = 0
            for var_match in var_matches:
                literal_part = original_operand[last_end:var_match.start()]
                if literal_part:
                    pattern_parts.append(re.escape(literal_part))
                var_name = var_match.group(1)
                replacement = self._variable_pattern(var_name, env_annotations)
                self_contained = False
                pattern_parts.append(replacement)
                last_end = var_match.end()
            remaining_literal = original_operand[last_end:]
            if remaining_literal:
                pattern_parts.append(re.escape(remaining_literal))
            pattern = "".join(pattern_parts)

        flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
        transform = ConstantTransform(RegularType(pattern, tainted=False))
        return PolymorphicCommandType(transform, self_contained=self_contained)
