from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import Constant
from rt.regular_types.stream_type import StreamType


class XargsStatResolver(RuleResolver):

    def resolve(
        self, invocation, user_annotations=None, env=None, heuristic_rules=None
    ):
        operands = self._get_operands(invocation)
        for operand, next_operand in zip(operands, operands[1:]):
            if operand == "-c":
                if next_operand == "%Y":
                    return CommandType(None, Constant(StreamType.from_pattern("[0-9]+")))
                if next_operand in {"%y", "%x"}:
                    return CommandType(None, Constant(StreamType.from_pattern(".*")))
        return super().resolve(invocation, None, env, None)


resolve = XargsStatResolver
