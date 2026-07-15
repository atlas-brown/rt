import re

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import Constant, Input, Reversal
from rt.regular_types.stream_type import StreamType


class RevResolver(RuleResolver):

    def resolve(
        self, invocation, user_annotations=None, env=None, heuristic_rules=None
    ):
        source = Input()
        if len(invocation.operand_list) > 0:
            file_type = self._file_from_env(env)
            source = Constant(file_type)
        return CommandType(None, Reversal(source))


resolve = RevResolver
