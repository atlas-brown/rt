import re
from dataclasses import dataclass
from typing import List

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import (
    Concatenation,
    Constant,
    Input,
    Replacement,
)
from rt.regular_types.stream_type import StreamType


@dataclass
class SedCommand:
    pass


@dataclass
class SubstituteCommand(SedCommand):
    pattern: str = ""
    replacement: str = ""
    flags: str = ""
    delimiter: str = "/"
    is_global: bool = False
    is_start_anchor: bool = False
    is_end_anchor: bool = False
    has_backreference: bool = False
    has_basic_capture_group: bool = False


@dataclass
class DeleteCommand(SedCommand):
    pass


@dataclass
class DeleteLineCommand(SedCommand):
    line_number: int


@dataclass
class PatternDeleteCommand(SedCommand):
    pattern: str


@dataclass
class UnknownCommand(SedCommand):
    raw_command: str = ""


@dataclass
class ParsedSedOperand:
    commands: List[SedCommand]

    @property
    def is_single_command(self) -> bool:
        return len(self.commands) == 1

    @property
    def primary_command(self) -> SedCommand:
        return self.commands[0] if self.commands else UnknownCommand()


def strip_quotes(string: str) -> str:
    if len(string) > 1:
        if string[-2] != "\\":
            if (string.startswith("'") and string.endswith("'")) or (
                string.startswith('"') and string.endswith('"')
            ):
                string = string[1:-1]
    return string


def has_unescaped_end_anchor(pattern: str) -> bool:
    if not pattern.endswith("$"):
        return False
    backslash_count = 0
    index = len(pattern) - 2
    while index >= 0 and pattern[index] == "\\":
        backslash_count += 1
        index -= 1
    return backslash_count % 2 == 0


def parse_substitute_command(operand: str, delimiter: str) -> SubstituteCommand:
    if not operand.startswith("s") or len(operand) < 2:
        raise ValueError(f"Invalid substitute command: {operand}")

    parts = operand.split(delimiter)
    if len(parts) < 3:
        raise ValueError(f"Invalid substitute command: {operand}")

    pattern = parts[0] if len(parts) > 0 else ""
    replacement = parts[1] if len(parts) > 1 else ""
    flags = parts[2] if len(parts) > 2 else ""

    if parts[0] == "s":
        pattern = parts[1] if len(parts) > 1 else ""
        replacement = parts[2] if len(parts) > 2 else ""
        flags = delimiter.join(parts[3:]) if len(parts) > 3 else ""

    raw_pattern = pattern
    raw_replacement = replacement

    is_start_anchor = pattern.startswith("^")
    is_exact_escaped_end_anchor = pattern == "\\$"
    is_end_anchor = is_exact_escaped_end_anchor or has_unescaped_end_anchor(pattern)

    if is_start_anchor:
        pattern = pattern[1:]
    if is_exact_escaped_end_anchor:
        pattern = ""
    elif is_end_anchor:
        pattern = pattern[:-1]

    pattern = pattern.replace("\\\\", "\\")
    pattern = strip_quotes(pattern)

    match = re.search(r"(\\+)$", pattern)
    if match and (len(match.group(1)) % 2 == 1):
        pattern = pattern + delimiter

    replacement = strip_quotes(replacement)
    is_global = "g" in flags

    return SubstituteCommand(
        pattern=pattern,
        replacement=replacement,
        flags=flags,
        delimiter=delimiter,
        is_global=is_global,
        is_start_anchor=is_start_anchor,
        is_end_anchor=is_end_anchor,
        has_backreference=_pattern_has_backreference(raw_replacement),
        has_basic_capture_group=_pattern_has_basic_capture_group(raw_pattern),
    )


def parse_delete_command(operand: str) -> SedCommand:
    if operand == "d":
        return DeleteCommand()
    elif operand.endswith("d") and operand[:-1].isdigit():
        line_number = int(operand[:-1])
        return DeleteLineCommand(line_number=line_number)
    elif operand.startswith("/"):
        pattern = operand[1:-2] if operand.endswith("/d") else operand[1:]
        return PatternDeleteCommand(pattern=pattern)
    else:
        raise ValueError(f"Invalid delete command: {operand}")


def parse_single_command(operand: str) -> SedCommand:
    if (
        operand == "d"
        or (operand.endswith("d") and operand[:-1].isdigit())
        or operand.startswith("/")
    ):
        return parse_delete_command(operand)

    if operand.startswith("s"):
        delimiter = operand[1] if len(operand) > 1 else None
        if not delimiter:
            raise ValueError("No delimiter found in substitute command")
        return parse_substitute_command(operand, delimiter)

    return UnknownCommand(raw_command=operand)


def parse_multiple_commands(operand: str) -> List[SedCommand]:
    commands = []
    current_cmd = ""
    i = 0
    in_substitute = False
    delimiter = None
    delimiter_count = 0

    while i < len(operand):
        char = operand[i]

        if char == "s" and (i == 0 or operand[i - 1] == ";"):
            in_substitute = True
            delimiter = operand[i + 1] if i + 1 < len(operand) else None
            delimiter_count = 0
            current_cmd += char
        elif in_substitute and char == delimiter:
            delimiter_count += 1
            current_cmd += char
            if delimiter_count >= 3:
                in_substitute = False
        elif char == ";" and not in_substitute:
            if current_cmd.strip():
                try:
                    parsed = parse_single_command(current_cmd.strip())
                    commands.append(parsed)
                except ValueError:
                    pass
            current_cmd = ""
        else:
            current_cmd += char

        i += 1

    if current_cmd.strip():
        try:
            parsed = parse_single_command(current_cmd.strip())
            commands.append(parsed)
        except ValueError:
            pass

    return commands


def parse_sed_operand(operand: str) -> ParsedSedOperand:
    if not operand:
        raise ValueError("Empty operand")

    if ";" in operand:
        commands = parse_multiple_commands(operand)
        return ParsedSedOperand(commands=commands)

    single_cmd = parse_single_command(operand)
    return ParsedSedOperand(commands=[single_cmd])


class SedResolver(RuleResolver):

    def _resolve_input_type(self, invocation, env, heuristic_rules=None):
        input_type, no_input_type = self._match_input_type(
            {fo.get_name() for fo in invocation.flag_option_list}
        )
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type

        try:
            operands = self._get_operands(invocation)
            if len(operands) == 0:
                raise ValueError("No operand provided for sed")
            parsed_operand = parse_sed_operand(operands[0])
            command = parsed_operand.primary_command
            if not isinstance(command, SubstituteCommand):
                return input_type, no_input_type
            pattern = self._pattern_for_input_constraint(command)
            if pattern is None:
                return input_type, no_input_type
            if command.has_backreference or command.has_basic_capture_group:
                return input_type, None

            no_input_type = (
                StreamType.from_pattern(".*")
                .concatenate(StreamType.from_pattern(pattern))
                .concatenate(StreamType.from_pattern(".*"))
                .complement()
            )
            no_input_type = StreamType(automaton=no_input_type.automaton)
            return input_type, no_input_type
        except Exception as error:
            if isinstance(error, ValueError):
                raise
            return input_type, None

    def resolve(
        self, invocation, user_annotations=None, env=None, heuristic_rules=None
    ):
        operands = self._get_operands(invocation)
        parsed_flags = set(
            map(lambda flag_option: flag_option.get_name(), invocation.flag_option_list)
        )
        if "-h" in parsed_flags or (len(operands) > 0 and operands[0] == "-h"):
            return CommandType(None, Constant(StreamType.from_pattern(".*")))
        if len(operands) == 0:
            raise ValueError("No operand provided for sed")
        operand = operands[0]

        try:
            parsed_operand = parse_sed_operand(operand)
            if parsed_operand.is_single_command and isinstance(
                parsed_operand.primary_command, DeleteCommand
            ):
                return CommandType(None, Constant(StreamType.from_pattern("")))
            if parsed_operand.is_single_command and isinstance(
                parsed_operand.primary_command, DeleteLineCommand
            ):
                return CommandType(None, Input())
            if not any(
                isinstance(command, SubstituteCommand)
                for command in parsed_operand.commands
            ):
                return super().resolve(invocation, None, env, None)

            transform = Input()

            for command in parsed_operand.commands:
                if isinstance(
                    command, (DeleteCommand, DeleteLineCommand, UnknownCommand)
                ):
                    continue
                if not isinstance(command, SubstituteCommand):
                    continue

                replacement = strip_quotes(command.replacement)
                replacement = _escape_literal_for_regular_type(replacement)
                replacement = replacement.replace("\\\\\\\\t", "\t")
                if command.has_backreference or "\\\\1" in replacement:
                    transform = Constant(StreamType.from_pattern(".*"))
                    continue

                if command.is_start_anchor and command.pattern == "":
                    if replacement:
                        transform = Concatenation(
                            Constant(StreamType.from_pattern(replacement)), transform
                        )
                    continue
                if command.is_end_anchor and command.pattern == "":
                    if replacement:
                        transform = Concatenation(
                            transform, Constant(StreamType.from_pattern(replacement))
                        )
                    continue

                pattern = self._pattern_for_matching(command)

                transform = Replacement(
                    transform,
                    pattern,
                    replacement,
                    first_occurence_only=not command.is_global,
                )

            return CommandType(None, transform)
        except Exception as error:
            if isinstance(error, ValueError):
                raise
            return CommandType(None, Input())

    @staticmethod
    def _is_exact_anchor_substitution(command: SubstituteCommand) -> bool:
        return command.pattern == "" and (
            command.is_start_anchor or command.is_end_anchor
        )

    @classmethod
    def _pattern_for_input_constraint(cls, command: SubstituteCommand) -> str | None:
        if cls._is_exact_anchor_substitution(command):
            return None
        if command.pattern.endswith("\\$"):
            pattern = strip_quotes(command.pattern[:-2])
            if command.is_start_anchor:
                pattern = "^" + pattern
            return pattern
        return cls._pattern_for_matching(command)

    @staticmethod
    def _pattern_for_matching(command: SubstituteCommand) -> str:
        pattern = strip_quotes(command.pattern)
        if command.is_start_anchor:
            pattern = "^" + pattern
        if command.is_end_anchor:
            pattern = pattern + "$"
        return pattern


def _pattern_has_backreference(pattern: str) -> bool:
    return re.search(r"(?<!\\)(?:\\\\)*\\[1-9]", pattern) is not None


def _pattern_has_basic_capture_group(pattern: str) -> bool:
    return "\\(" in pattern or "\\)" in pattern


def _escape_literal_for_regular_type(string: str) -> str:
    """Escape a string so it is treated as a literal in regex replacement.

    First applies re.escape() to escape all regex metacharacters, then converts
    the escaped ``$``, ``{``, ``}`` characters from backslash-escaped form to
    character-class form (e.g. ``[$]`` instead of ``\\$``). This prevents regex
    engines from interpreting ``$`` as an end-of-line anchor and ``{n}`` as a
    repetition quantifier in replacement strings.
    """

    return (
        re.escape(string)
        .replace("\\$", "[$]")
        .replace("\\{", "[{]")
        .replace("\\}", "[}]")
    )


resolve = SedResolver
