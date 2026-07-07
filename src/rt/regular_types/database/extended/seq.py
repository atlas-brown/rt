import re

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import Constant
from rt.regular_types.stream_type import StreamType


class SeqResolver(RuleResolver):

    def resolve(
        self, invocation, user_annotations=None, env=None, heuristic_rules=None
    ):
        operands = self._get_operands(invocation)
        if len(operands) == 0:
            raise ValueError("No operand provided for seq")
        line_type = None
        if len(operands) == 1 and operands[0].isdigit():
            if int(operands[0]) <= 0:
                line_type = StreamType.from_pattern("")
            else:
                line_type = StreamType.from_pattern("[0-9]+")
        if len(operands) == 2 and operands[0].isdigit():
            if int(operands[0]) < 0:
                line_type = StreamType.from_pattern("-?[0-9]+")
            else:
                line_type = StreamType.from_pattern("[0-9]+")

        flags = set()
        flag_args = {}
        for flag in invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, "get_arg") and flag.get_arg():
                flag_args[name] = flag.get_arg()

        delimiter = "\n"
        if "-s" in flags:
            delimiter = f"{flag_args['-s']}"

        while (
            (delimiter[0] == "(" and delimiter[-1] == ")")
            or (delimiter[0] == "[" and delimiter[-1] == "]")
            or (delimiter[0] == "'" and delimiter[-1] == "'")
            or (delimiter[0] == '"' and delimiter[-1] == '"')
        ):
            delimiter = delimiter[1:-1]
        delimiter = delimiter[-1]

        if delimiter == "\n" and line_type is not None:
            return CommandType(None, Constant(line_type))
        if delimiter != "\n" and line_type is not None:
            sep = StreamType.from_pattern(re.escape(delimiter))
            out = line_type.concatenate(sep.concatenate(line_type).repeat(0, None))
            return CommandType(None, Constant(out))

        return super().resolve(invocation, None, env, None)


resolve = SeqResolver
