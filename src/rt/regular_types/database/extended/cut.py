import re

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import Constant, FieldExtraction, Input
from rt.regular_types.stream_type import StreamType


class CutResolver(RuleResolver):

    def resolve(
        self, invocation, user_annotations=None, env=None, heuristic_rules=None
    ):
        source = Input()
        if len(invocation.operand_list) > 0:
            file_name = invocation.operand_list[0].name
            annotated = self._annotated_content_type(0, env)
            if annotated is None:
                annotated = StreamType.from_pattern(".*")
            source = Constant(annotated)

        flags = set()
        flag_args = {}
        for flag in invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, "get_arg") and flag.get_arg():
                flag_args[name] = flag.get_arg()

        try:
            if flags == {"-b"} or flags == {"-c"}:
                flag_arg = flag_args.get("-c") if "-c" in flags else flag_args.get("-b")
                indices, _ = preprocess(flag_arg)
                transform = FieldExtraction(source, "", indices, False)
            elif flags == {"-f"} or flags == {"-d", "-f"}:
                flag_arg = flag_args.get("-f")
                delimiter = "\t"
                if "-d" in flags:
                    delimiter = f"{flag_args['-d']}"
                indices, _ = preprocess(flag_arg)
                transform = FieldExtraction(source, delimiter, indices, False)
            else:
                transform = Constant(StreamType.from_pattern(".*"))
        except Exception:
            transform = Constant(StreamType.from_pattern(".*"))

        return CommandType(None, transform)


def preprocess(arg: str) -> tuple[list[int], bool]:
    if not arg:
        return [], False

    if "${" in arg or "$(" in arg:
        return [], False

    result = []
    parts = arg.split(",")
    has_upperbound = True
    no_upperbound_start = float("inf")

    for part in parts:
        if "-" in part:
            range_parts = part.split("-")
            if len(range_parts) != 2:
                raise ValueError(f"invalid range format: {part}")

            start, end = range_parts
            if not start:
                start = 1
            if not end:
                has_upperbound = False
                end = -1

            try:
                start, end = int(start), int(end)
                if end == -1:
                    no_upperbound_start = int(min(start, no_upperbound_start))
                else:
                    result.extend(range(start, end + 1))
            except ValueError:
                raise ValueError(f"invalid range values: {part}")

        else:
            try:
                result.append(int(part))
            except ValueError:
                raise ValueError(f"invalid field number: {part}")
    if not has_upperbound:
        result = [x for x in result if x < no_upperbound_start]
        result.append(no_upperbound_start)

    return result, has_upperbound


resolve = CutResolver
