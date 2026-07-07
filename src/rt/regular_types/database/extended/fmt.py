import re

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import (
    CharTranslation,
    Concatenation,
    Constant,
    Input,
    Intersection,
)
from rt.regular_types.stream_type import StreamType


class FmtResolver(RuleResolver):

    def resolve(
        self, invocation, user_annotations=None, env=None, heuristic_rules=None
    ):
        flags = set()
        flag_args = {}
        for flag in invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, "get_arg") and flag.get_arg():
                flag_args[name] = flag.get_arg()

        if "-w" in flags:
            width = int(flag_args["-w"])
            if width == 1:
                base = Intersection(
                    CharTranslation(Input(), " \t", "\n", False, False),
                    Constant(StreamType.from_pattern(".+")),
                )
                transform = Concatenation(Constant(StreamType.from_pattern(" *")), base)
                return CommandType(None, transform)

        return super().resolve(invocation, None, env, None)


resolve = FmtResolver
