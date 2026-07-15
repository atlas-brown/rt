import re

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import (
    Complement,
    Concatenation,
    Constant,
    Input,
    Intersection,
)
from rt.regular_types.stream_type import StreamType


def _has_start_anchor(pattern: str) -> bool:
    return pattern.startswith("^")


def _has_end_anchor(pattern: str) -> bool:
    return pattern.endswith("$")


def _without_anchors(pattern: str) -> str:
    if pattern.startswith("^"):
        pattern = pattern[1:]
    if pattern.endswith("$"):
        pattern = pattern[:-1]
    return pattern


class GrepResolver(RuleResolver):

    @staticmethod
    def _normalized_operands(invocation):
        operands = [operand.name for operand in invocation.operand_list]
        if operands and operands[0] == "--":
            return operands[1:], True
        return operands, False

    @staticmethod
    def _contains_shell_expansion(pattern: str) -> bool:
        return (
            re.search(r"(\$\{.*?\}|\$[a-zA-Z_][a-zA-Z0-9_]*|\$\()", pattern) is not None
        )

    @staticmethod
    def _patterns_from_e_flags(
        flag_args: dict[str, list[str]], operands: list[str]
    ) -> list[str]:
        patterns = list(flag_args.get("-e", []))
        if not patterns and operands:
            patterns = [operands[0]]
        return patterns

    @classmethod
    def _parsed_flags_and_operands(cls, invocation):
        operands, has_double_dash = cls._normalized_operands(invocation)
        operands = list(operands)
        flags = set()
        flag_args: dict[str, list[str]] = {}

        for flag in invocation.flag_option_list:
            name = flag.get_name()
            arg = flag.get_arg() if hasattr(flag, "get_arg") else None

            if (
                name == "-f"
                and arg
                and arg.startswith("-")
                and len(arg) > 1
                and operands
            ):
                flags.add("-f")
                for option_char in arg[1:]:
                    flags.add(f"-{option_char}")
                flag_args.setdefault("-f", []).append(operands[0])
                operands = operands[1:]
                continue

            flags.add(name)
            if arg:
                flag_args.setdefault(name, []).append(arg)

        return flags, flag_args, operands, has_double_dash

    def resolve(
        self, invocation, user_annotations=None, env=None, heuristic_rules=None
    ):
        source = Input()
        flags, flag_args, normalized_operands, has_double_dash = (
            self._parsed_flags_and_operands(invocation)
        )

        if len(normalized_operands) > 1 or (
            len(normalized_operands) == 1 and ("-e" in flags or "-f" in flags)
        ):
            file_type = self._file_from_env(env)
            source = Constant(file_type)

        if "-f" in flags and "-o" not in flags:
            if "-c" in flags:
                return CommandType(None, Constant(StreamType.from_pattern("[0-9]+")))
            return CommandType(None, source)

        if "-e" in flags:
            patterns = self._patterns_from_e_flags(flag_args, normalized_operands)
            if not patterns:
                return CommandType(None, source)

            pattern_st = StreamType.from_pattern(patterns[0])
            original_pattern = patterns[0]
            for arg in patterns[1:]:
                arg = arg.replace("\\\\", "\\")
                pattern_st = pattern_st.union(StreamType.from_pattern(arg))
                original_pattern = arg
        else:
            if len(normalized_operands) == 0 and "-f" not in flags:
                raise ValueError("No pattern provided for grep")
            if len(normalized_operands) == 0:
                return CommandType(None, source)
            pattern = normalized_operands[0]
            if pattern.startswith("--") and not has_double_dash:
                raise ValueError("Pattern cannot start with '--'")
            pattern = pattern.replace("\\\\", "\\")
            if "-F" in flags:
                pattern = re.escape(pattern)
            pattern_st = StreamType.from_pattern(pattern)
            original_pattern = pattern

        if "-c" in flags:
            return CommandType(None, Constant(StreamType.from_pattern("[0-9]+")))

        if "-o" not in flags:
            if not _has_start_anchor(original_pattern):
                pattern_st = StreamType.from_pattern(".*").concatenate(pattern_st)
            if not _has_end_anchor(original_pattern):
                pattern_st = pattern_st.concatenate(StreamType.from_pattern(".*"))
            pattern_node = Constant(pattern_st)
            transform = Intersection(source, pattern_node)
        else:
            if not _has_start_anchor(original_pattern) and not _has_end_anchor(
                original_pattern
            ):
                return CommandType(None, Constant(pattern_st))
            transform = Intersection(source, Constant(pattern_st))

        if "-w" in flags:
            word_pattern = (
                StreamType.from_pattern("(.*[^a-zA-Z0-9_])?")
                .concatenate(pattern_st)
                .concatenate(StreamType.from_pattern("([^a-zA-Z0-9_].*)?"))
            )
            transform = Intersection(source, Constant(word_pattern))
        if "-v" in flags:
            transform = Intersection(source, Complement(Constant(pattern_st)))
        if "-n" in flags:
            transform = Concatenation(
                Constant(StreamType.from_pattern("[0-9]+:")), transform
            )

        return CommandType(None, transform)


resolve = GrepResolver
