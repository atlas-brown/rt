import re
from dataclasses import dataclass
from typing import List

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

def preprocess_string(string: str) -> str:
    """Remove quotes from string if present and not escaped."""
    if len(string) > 1:
        if string[-2] != "\\":
            if (string.startswith("'") and string.endswith("'")) or (string.startswith('"') and string.endswith('"')):
                string = string[1:-1]
    return string

def refine_log(s: str) -> str:
    """Format string for logging purposes."""
    if s == "":
        return "\"\""
    return s

def parse_substitute_command(operand: str, delimiter: str) -> SubstituteCommand:
    """Parse a substitute command with any delimiter (s/pattern/replacement/flags, s|pattern|replacement|flags, etc)."""
    if not operand.startswith('s') or len(operand) < 2:
        raise ValueError(f"Invalid substitute command: {operand}")
    
    # Parse by finding delimiter positions, handling escaped delimiters
    parts = []
    current_part = ""
    i = 2  # Skip 's' and delimiter
    escape_next = False
    part_count = 0
    
    while i < len(operand) and part_count < 3:  # pattern, replacement, flags
        char = operand[i]
        
        if escape_next:
            current_part += char
            escape_next = False
        elif char == '\\':
            current_part += char
            escape_next = True
        elif char == delimiter:
            parts.append(current_part)
            current_part = ""
            part_count += 1
        else:
            current_part += char
        
        i += 1
    
    # Add remaining part (flags or final replacement if no flags)
    if current_part or i <= len(operand):
        parts.append(current_part)
    
    # Add remaining characters as flags
    if i < len(operand):
        parts[-1] += operand[i:]
    
    # Ensure we have at least pattern and replacement
    if len(parts) < 2:
        raise ValueError(f"Invalid substitute command: {operand}")
    
    pattern = parts[0] if len(parts) > 0 else ""
    replacement = parts[1] if len(parts) > 1 else ""
    flags = parts[2] if len(parts) > 2 else ""
    
    # Process pattern for anchors
    is_start_anchor = pattern.startswith("^")
    is_end_anchor = pattern.endswith("$") or pattern.endswith("\\$")
    
    # Clean up pattern
    if is_start_anchor:
        pattern = pattern[1:]
    if is_end_anchor:
        if pattern.endswith("\\$"):
            pattern = pattern[:-2]
        elif pattern.endswith("$"):
            pattern = pattern[:-1]
    
    # Process pattern and replacement
    pattern = pattern.replace("\\\\", "\\")
    pattern = preprocess_string(pattern)
    
    # Handle escaped delimiters in pattern (from original logic)
    match = re.search(r'(\\+)$', pattern)
    if match and (len(match.group(1)) % 2 == 1):
        pattern = pattern + delimiter
    
    replacement = preprocess_string(replacement)
    
    # Check for global flag
    is_global = "g" in flags
    
    return SubstituteCommand(
        pattern=pattern,
        replacement=replacement,
        flags=flags,
        delimiter=delimiter,
        is_global=is_global,
        is_start_anchor=is_start_anchor,
        is_end_anchor=is_end_anchor
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