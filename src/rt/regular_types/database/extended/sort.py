import re

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import Constant
from rt.regular_types.stream_type import StreamType


class SortResolver(RuleResolver):

    def resolve(
        self, invocation, user_annotations=None, env=None, heuristic_rules=None
    ):
        if len(invocation.operand_list) > 0:
            return CommandType(None, Constant(StreamType.from_pattern(".*")))
        return super().resolve(invocation, None, env, None)


resolve = SortResolver
