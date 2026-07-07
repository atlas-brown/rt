import re

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import Concatenation, Constant, Input, Repetition
from rt.regular_types.stream_type import StreamType


class PasteResolver(RuleResolver):

    def _resolve_input_type(self, invocation, env, heuristic_rules=None):
        input_type, no_input_type = self._match_input_type(
            {fo.get_name() for fo in invocation.flag_option_list}
        )
        if len(invocation.operand_list) != 0:
            return StreamType.from_pattern(".*"), None
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type

        parsed_flags = set(
            map(lambda flag_option: flag_option.get_name(), invocation.flag_option_list)
        )
        if "-s" not in parsed_flags:
            return input_type, StreamType.from_pattern(".*")

        return input_type, no_input_type

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
