import re

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver, _substitute_shell_vars
from rt.regular_types.stream_transform import Constant
from rt.regular_types.stream_type import StreamType


class EchoResolver(RuleResolver):

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
                replacement = _substitute_shell_vars(var_name, env)
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
