import re

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import Constant
from rt.regular_types.stream_type import StreamType


class SortResolver(RuleResolver):

    def _resolve_input_type(self, invocation, env, heuristic_rules=None):
        if len(invocation.operand_list) > 0:
            return StreamType.from_pattern(".*"), None
        input_type, no_input_type = self._match_input_type(
            {fo.get_name() for fo in invocation.flag_option_list}
        )
        flags = set()
        flag_args: dict[str, list[str]] = {}
        for flag in invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, "get_arg") and flag.get_arg():
                if name not in flag_args:
                    flag_args[name] = []
                flag_args[name].append(flag.get_arg())

        if "-k" not in flags:
            return input_type, no_input_type

        acc_input = StreamType.from_pattern(".*")
        args = flag_args.get("-k")
        for arg in args:
            flag = (
                "".join(list(re.finditer(r"[^\d]+$", arg))[0].group())
                if re.search(r"[^\d]+$", arg)
                else ""
            )
            arg = arg.replace(flag, "")
            if "," in arg:
                if flag == "":
                    field, start = arg.split(",")
                    try:
                        field, start = int(field), int(start)
                    except Exception as e:
                        return StreamType.from_pattern(".*"), None
                    pattern = f"[\t ]*([^\t ]+[\t ]+){{{field - 1}}}[^\t ]{{{start}}}.*"
                    acc_input = acc_input.intersect(StreamType.from_pattern(pattern))
                else:
                    field, start = arg.split(",")
                    try:
                        field, start = int(field), int(start)
                    except Exception as e:
                        return StreamType.from_pattern(".*"), None
                    if "n" in flag:
                        pattern = f"[\t ]*([^\t ]+[\t ]+){{{field - 1}}}[0-9].*"
                        acc_input = acc_input.intersect(StreamType.from_pattern(pattern))
            else:
                if flag == "":
                    field = int(arg)
                    pattern = f"[\t ]*([^\t ]+[\t ]+){{{field - 1}}}[^\t ]+.*"
                    acc_input = acc_input.intersect(StreamType.from_pattern(pattern))
                else:
                    field = int(arg)
                    if "n" in flag:
                        pattern = f"[\t ]*([^\t ]+[\t ]+){{{field - 1}}}[0-9]+.*"
                        acc_input = acc_input.intersect(StreamType.from_pattern(pattern))

        return acc_input, None

    def resolve(
        self, invocation, user_annotations=None, env=None, heuristic_rules=None
    ):
        if len(invocation.operand_list) > 0:
            return CommandType(None, Constant(StreamType.from_pattern(".*")))
        return super().resolve(invocation, None, env, None)


resolve = SortResolver
