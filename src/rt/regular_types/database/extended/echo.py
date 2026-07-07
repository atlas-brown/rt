import re

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import Constant
from rt.regular_types.stream_type import StreamType
from rt.type_checking.annotations import EnvAnnotationKind


class EchoResolver(RuleResolver):

    @staticmethod
    def _variable_pattern(token: str, env) -> str:
        candidate_keys = [token]
        if token.startswith("${") and token.endswith("}"):
            candidate_keys.append(f"${token[2:-1]}")
        elif token.startswith("$") and len(token) > 1:
            candidate_keys.append("${" + token[1:] + "}")

        annotations = env.get("__annotations__", {})
        for key in candidate_keys:
            for annot in annotations.get(key, []):
                if annot.kind == EnvAnnotationKind.VAR:
                    return annot.regex
        return "[^\n]*"

    def resolve(
        self, invocation, user_annotations=None, env=None, heuristic_rules=None
    ):
        self_contained = True
        operands = self._get_operands(invocation)
        if len(operands) == 0:
            raise ValueError("No operand provided for echo")

        original_operand = operands[0]
        var_matches = list(
            re.finditer(r"(\$\{.*?\}|\$[a-zA-Z_][a-zA-Z0-9_]*)", original_operand)
        )
        if not var_matches:
            pattern = re.escape(original_operand)
        else:
            pattern_parts = []
            last_end = 0
            for var_match in var_matches:
                literal_part = original_operand[last_end : var_match.start()]
                if literal_part:
                    pattern_parts.append(re.escape(literal_part))
                var_name = var_match.group(1)
                replacement = self._variable_pattern(var_name, env)
                self_contained = False
                pattern_parts.append(replacement)
                last_end = var_match.end()
            remaining_literal = original_operand[last_end:]
            if remaining_literal:
                pattern_parts.append(re.escape(remaining_literal))
            pattern = "".join(pattern_parts)

        output = StreamType.from_pattern(pattern)
        if self_contained:
            return CommandType(None, Constant(output))
        return CommandType(None, Constant(output))


resolve = EchoResolver
