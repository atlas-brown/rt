import re

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import Concatenation, Constant, Input, Repetition
from rt.regular_types.stream_type import StreamType


class PasteResolver(RuleResolver):

    def resolve(
        self, invocation, user_annotations=None, env=None, heuristic_rules=None
    ):
        flags = set()
        flag_args: dict[str, list[str]] = {}
        for flag in invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, "get_arg") and flag.get_arg():
                if name not in flag_args:
                    flag_args[name] = []
                flag_args[name].append(flag.get_arg())
        if "-s" in flags:
            delimiter = "\t"
            if "-d" in flags:
                delimiter = flag_args['-d'][0]

            while (
                (delimiter[0] == "(" and delimiter[-1] == ")")
                or (delimiter[0] == "[" and delimiter[-1] == "]")
                or (delimiter[0] == "'" and delimiter[-1] == "'")
                or (delimiter[0] == '"' and delimiter[-1] == '"')
            ):
                delimiter = delimiter[1:-1]

            delimiter = delimiter[-1]
            separator = Constant(StreamType.from_pattern(f"[{delimiter}]"))
            transform = Concatenation(
                Input(), Repetition(Concatenation(separator, Input()), 0, None)
            )
            return CommandType(None, transform)
        return super().resolve(invocation, None, env, None)


resolve = PasteResolver
