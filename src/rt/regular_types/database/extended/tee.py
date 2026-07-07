from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import Constant, DefaultIfEmpty, Input
from rt.regular_types.stream_type import StreamType


class TeeResolver(RuleResolver):
    def resolve(
        self, invocation, user_annotations=None, env=None, heuristic_rules=None
    ):
        transform = DefaultIfEmpty(Input(), Constant(StreamType.from_pattern(".*")))
        return CommandType(None, transform)


resolve = TeeResolver
