from dataclasses import dataclass
from typing import List

from stream.regex_parser import (
    escape_literal_for_regular_type,
    has_backreference,
    has_basic_capture_group,
)

@dataclass
class SedCommand:
    """Base class for individual sed commands."""
    pass

@dataclass
class SubstituteCommand(SedCommand):
    """A parsed substitute command."""
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
    """A parsed delete command (general delete)."""
    pass

@dataclass
class DeleteLineCommand(SedCommand):
    """A parsed line-specific delete command."""
    line_number: int

@dataclass
class PatternDeleteCommand(SedCommand):
    """A parsed pattern-based delete command."""
    pattern: str

@dataclass
class UnknownCommand(SedCommand):
    """An unknown or unsupported sed command."""
    raw_command: str = ""

@dataclass
class ParsedSedOperand:
    """Container for all parsed sed commands in order."""
    commands: List[SedCommand]

    @property
    def is_single_command(self) -> bool:
        """True if this operand contains only one command."""
        return len(self.commands) == 1

    @property
    def primary_command(self) -> SedCommand:
        """Returns the first command."""
        return self.commands[0] if self.commands else UnknownCommand()

def strip_quotes(string: str) -> str:
    """Remove quotes from string if present and not escaped."""
    if len(string) > 1:
        if string[-2] != "\\":
            if (string.startswith("'") and string.endswith("'")) or (string.startswith('"') and string.endswith('"')):
                string = string[1:-1]
    return string

def has_unescaped_end_anchor(pattern: str) -> bool:
    """Return True when pattern ends in a dollar not escaped by a backslash."""
    if not pattern.endswith("$"):
        return False

    backslash_count = 0
    index = len(pattern) - 2
    while index >= 0 and pattern[index] == "\\":
        backslash_count += 1
        index -= 1
    return backslash_count % 2 == 0

def parse_substitute_command(operand: str, delimiter: str) -> SubstituteCommand:
    """Parse a substitute command with any delimiter (s/pattern/replacement/flags, s|pattern|replacement|flags, etc)."""
    if not operand.startswith('s') or len(operand) < 2:
        raise ValueError(f"Invalid substitute command: {operand}")

    # Keep the field boundaries used by the existing type-inference semantics:
    # escaped delimiters are repaired in the pattern below instead of shifting
    # all parsing responsibility to the signature.
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

    # Process pattern for anchors. A bare \s/\$/.../ is treated as the
    # end-anchor suffix form used by the previous command-type logic, but
    # non-exact patterns like s/#.*\$// keep the escaped dollar literal.
    is_start_anchor = pattern.startswith("^")
    is_exact_escaped_end_anchor = pattern == "\\$"
    is_end_anchor = is_exact_escaped_end_anchor or has_unescaped_end_anchor(pattern)

    # Clean up pattern
    if is_start_anchor:
        pattern = pattern[1:]
    if is_exact_escaped_end_anchor:
        pattern = ""
    elif is_end_anchor:
        pattern = pattern[:-1]

    # Process pattern and replacement
    pattern = pattern.replace("\\\\", "\\")
    pattern = strip_quotes(pattern)
    replacement = strip_quotes(replacement)

    # Check for global flag
    is_global = "g" in flags

    return SubstituteCommand(
        pattern=pattern,
        replacement=replacement,
        flags=flags,
        delimiter=delimiter,
        is_global=is_global,
        is_start_anchor=is_start_anchor,
        is_end_anchor=is_end_anchor,
        has_backreference=has_backreference(raw_replacement),
        has_basic_capture_group=has_basic_capture_group(raw_pattern),
    )

def parse_delete_command(operand: str) -> SedCommand:
    """Parse a delete command (d or line_number d)."""
    if operand == "d":
        return DeleteCommand()
    elif operand.endswith("d") and operand[:-1].isdigit():
        line_number = int(operand[:-1])
        return DeleteLineCommand(line_number=line_number)
    elif operand.startswith("/"):
        # Pattern-based delete
        pattern = operand[1:-2] if operand.endswith("/d") else operand[1:]
        return PatternDeleteCommand(pattern=pattern)
    else:
        raise ValueError(f"Invalid delete command: {operand}")

def parse_single_command(operand: str) -> SedCommand:
    """Parse a single sed command (no semicolons) and return the command object."""
    # Handle delete commands
    if operand == "d" or (operand.endswith("d") and operand[:-1].isdigit()) or operand.startswith("/"):
        return parse_delete_command(operand)

    # Handle substitute commands
    if operand.startswith("s"):
        delimiter = operand[1] if len(operand) > 1 else None
        if not delimiter:
            raise ValueError("No delimiter found in substitute command")

        return parse_substitute_command(operand, delimiter)

    # Unknown command type - create an unknown command
    return UnknownCommand(raw_command=operand)

def parse_multiple_commands(operand: str) -> List[SedCommand]:
    """
    Parse multiple sed commands separated by semicolons, maintaining order.

    Examples:
        "s/a/b/;s/c/d/" -> [substitute(a->b), substitute(c->d)]
        "s/a/b/g;d" -> [substitute(a->b, global), delete]
        "d;s/a/b/" -> [delete, substitute(a->b)]  # Different from above!
    """
    commands = []
    current_cmd = ""
    i = 0
    in_substitute = False
    delimiter = None
    delimiter_count = 0

    while i < len(operand):
        char = operand[i]

        if char == 's' and (i == 0 or operand[i-1] == ';'):
            in_substitute = True
            delimiter = operand[i+1] if i+1 < len(operand) else None
            delimiter_count = 0
            current_cmd += char
        elif in_substitute and char == delimiter:
            delimiter_count += 1
            current_cmd += char
            # After 3 delimiters (pattern|replacement|flags), we're done with substitute
            if delimiter_count >= 3:
                in_substitute = False
        elif char == ';' and not in_substitute:
            if current_cmd.strip():
                try:
                    parsed = parse_single_command(current_cmd.strip())
                    commands.append(parsed)
                except ValueError:
                    pass  # Skip invalid commands
            current_cmd = ""
        else:
            current_cmd += char

        i += 1

    # Parse the last command
    if current_cmd.strip():
        try:
            parsed = parse_single_command(current_cmd.strip())
            commands.append(parsed)
        except ValueError:
            pass  # Skip invalid commands

    return commands

def parse_sed_operand(operand: str) -> ParsedSedOperand:
    """
    Parse a sed operand and return a structured representation with commands in order.

    Args:
        operand: The sed operand string (e.g., "s/pattern/replacement/g", "d", "5d", "s|a|b|;s/c/d/")

    Returns:
        ParsedSedOperand: Container with all commands in execution order

    Examples:
        "s/a/b/;d" -> ParsedSedOperand([substitute(a->b), delete])
        "d;s/a/b/" -> ParsedSedOperand([delete, substitute(a->b)])  # Different!
        "s/a/b/;s/c/d/;d" -> ParsedSedOperand([substitute(a->b), substitute(c->d), delete])
    """
    if not operand:
        raise ValueError("Empty operand")

    # Check for multiple commands first (semicolon-separated)
    if ";" in operand:
        commands = parse_multiple_commands(operand)
        return ParsedSedOperand(commands=commands)

    # Single command
    single_cmd = parse_single_command(operand)
    return ParsedSedOperand(commands=[single_cmd])


# Test cases demonstrating proper command ordering:
"""
CRITICAL: Command order matters in sed!

The parser now correctly maintains command execution order:

1. Different delimiters:
   - parse_sed_operand("s/old/new/g")  # Standard slash delimiter
   - parse_sed_operand("s|old|new|g")  # Pipe delimiter
   - parse_sed_operand("s@old@new@g")  # At-sign delimiter
   - parse_sed_operand("s:old:new:g")  # Colon delimiter

2. Order-dependent command sequences:
   - parse_sed_operand("s/a/b/;d") -> [substitute(a->b), delete]
   - parse_sed_operand("d;s/a/b/") -> [delete, substitute(a->b)]  # DIFFERENT!
   - parse_sed_operand("s/a/b/;s/c/d/;d") -> [subst, subst, delete]
   - parse_sed_operand("d;s/a/b/;s/c/d/") -> [delete, subst, subst]

3. Why order matters:
   - "s/a/b/;d" applies substitution THEN deletes -> substitution can affect text
   - "d;s/a/b/" deletes THEN tries substitution -> substitution never runs!
   - "s/a/X/;s/X/b/" -> replaces a->X then X->b (result: a->b)
   - "s/X/b/;s/a/X/" -> replaces X->b then a->X (result: a->X, no chaining)

4. Mixed command types (order preserved):
   - parse_sed_operand("5d;s/error/warning/g;3d") -> [delete_line(5), substitute, delete_line(3)]
   - parse_sed_operand("s/old/new/;/pattern/d;s/bad/good/") -> [substitute, pattern_delete, substitute]

5. Complex real-world examples:
   - "s/^/> /;s/$/</;d" -> [add_prefix, add_suffix, delete_all]
   - "1d;s/header/title/g;$d" -> [delete_first, substitute_global, delete_last]
"""

from stream.command_signature import CommandSignature
from stream.command_type import PolymorphicCommandType
from stream.regular_type import RegularType
from stream.transformation_ast import ALPHA, ConcatenateTransform, ConstantTransform, TaintTransform, TranslateMatchTransform
from stream.tool_error import ToolError

class SedSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations):
        input_type, no_input_type = super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type

        try:
            operands = super().get_operands(parsed_command_invocation)
            if len(operands) == 0:
                raise ToolError("No operand provided for sed")
            parsed_operand = parse_sed_operand(operands[0])
            command = parsed_operand.primary_command
            if not isinstance(command, SubstituteCommand):
                return input_type, no_input_type
            pattern = self._pattern_for_input_constraint(command)
            if pattern is None:
                return input_type, no_input_type
            if command.has_backreference or command.has_basic_capture_group:
                return input_type, None

            no_input_type = ~(RegularType(".*") + RegularType(pattern) + RegularType(".*"))
            no_input_type.tainted = False
            return input_type, no_input_type
        except Exception as error:
            if isinstance(error, ToolError):
                raise
            return input_type, None

    def construct_command_type(self, parsed_command_invocation, env_annotations):
        operands = super().get_operands(parsed_command_invocation)
        parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
        mode = "extended" if "-E" in parsed_flags or "-r" in parsed_flags else "basic"
        if "-h" in parsed_flags or (len(operands) > 0 and operands[0] == "-h"):
            return PolymorphicCommandType(ConstantTransform(RegularType(".*")), self_contained=True)
        if len(operands) == 0:
            raise ToolError("No operand provided for sed")
        operand = operands[0]

        try:
            parsed_operand = parse_sed_operand(operand)
            if (
                parsed_operand.is_single_command
                and isinstance(parsed_operand.primary_command, DeleteCommand)
            ):
                return PolymorphicCommandType(ConstantTransform(RegularType("")), self_contained=True)
            if (
                parsed_operand.is_single_command
                and isinstance(parsed_operand.primary_command, DeleteLineCommand)
            ):
                return PolymorphicCommandType(ALPHA, self_contained=True)
            if not any(isinstance(command, SubstituteCommand) for command in parsed_operand.commands):
                return super().construct_command_type(parsed_command_invocation, env_annotations)

            transform = ALPHA
            tainted = False

            for command in parsed_operand.commands:
                if isinstance(command, (DeleteCommand, DeleteLineCommand, UnknownCommand)):
                    continue
                if not isinstance(command, SubstituteCommand):
                    continue

                replacement = strip_quotes(command.replacement)
                replacement = escape_literal_for_regular_type(replacement)
                replacement = replacement.replace("\\\\\\\\t", "\t")
                if command.has_backreference or "\\\\1" in replacement:
                    transform = ConstantTransform(RegularType(".*"))
                    continue
                if "\\\\" in replacement:
                    tainted = True

                if command.is_start_anchor and command.pattern == "":
                    if replacement:
                        transform = ConcatenateTransform(ConstantTransform(RegularType(replacement, tainted=False)), transform)
                    continue
                if command.is_end_anchor and command.pattern == "":
                    if replacement:
                        transform = ConcatenateTransform(transform, ConstantTransform(RegularType(replacement, tainted=False)))
                    continue

                pattern = self._pattern_for_matching(command)

                transform = TranslateMatchTransform(
                    transform,
                    pattern,
                    replacement,
                    global_match=command.is_global,
                    mode=mode,
                )

            if tainted:
                transform = TaintTransform(transform, True)
            return PolymorphicCommandType(transform, self_contained=True)
        except Exception as error:
            if isinstance(error, ToolError):
                raise
            return PolymorphicCommandType(TaintTransform(ALPHA, True), self_contained=False)

    @staticmethod
    def _is_exact_anchor_substitution(command: SubstituteCommand) -> bool:
        return command.pattern == "" and (command.is_start_anchor or command.is_end_anchor)

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
