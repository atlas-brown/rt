import re

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import Constant, Input
from rt.regular_types.stream_type import StreamType


class TailResolver(RuleResolver):

    def resolve(
        self, invocation, user_annotations=None, env=None, heuristic_rules=None
    ):
        source = Input()
        if len(invocation.operand_list) > 0:
            file_type = self._file_from_env(env)
            source = Constant(file_type)

        flags = set()
        flag_args: dict[str, list[str]] = {}
        for flag in invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, "get_arg") and flag.get_arg():
                if name not in flag_args:
                    flag_args[name] = []
                flag_args[name].append(flag.get_arg())
        if "-n" in flags:
            try:
                return CommandType(None, source)
            except Exception:
                return CommandType(None, Constant(StreamType.from_pattern(".*")))
        return super().resolve(invocation, None, env, None)


resolve = TailResolver
