import logging
import re
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
            operand = operands[0]
            if not operand.startswith("s"):
                return input_type, no_input_type
            delimiter = operand[1]
            parts = operand.split(delimiter)
            if len(parts) < 3:
                return input_type, no_input_type
            if parts[1] == '^' or parts[1] == '\\$' or parts[1] == '$':
                return input_type, no_input_type
            # Fixme: handle start and end anchors
            if parts[0] == 's':
                parts[1] = parts[1].replace("\\\\", "\\")
                parts[1] = preprocess(parts[1])
                match = re.search(r'(\\+)$', parts[1])
                if match and (len(match.group(1)) % 2 == 1):
                    parts[1] = parts[1] + delimiter
                if parts[1].endswith("$"):
                    parts[1] = parts[1][:-2]
                no_input_type = ~(RegularType(".*") + RegularType(parts[1]) + RegularType(".*"))
                no_input_type.tainted = False
                return input_type, no_input_type
            return input_type, no_input_type
        except Exception as error:
            if isinstance(error, ToolError):
                raise
            logging.debug("Falling back to unconstrained sed input type for operand %r: %s", parsed_command_invocation, error, exc_info=True)
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
        if operand == "d":
            return PolymorphicCommandType(ConstantTransform(RegularType("")), self_contained=True)
        if operand[-1] == "d" and operand[:-1].isdigit():
            return PolymorphicCommandType(ALPHA, self_contained=True)
        if not operand.startswith("s"):
            return super().construct_command_type(parsed_command_invocation, env_annotations)

        try:
            delimiter = operand[1]
            parts = operand.split(delimiter)
            segments = [operand]
            if len(parts) < 3:
                return super().construct_command_type(parsed_command_invocation, env_annotations)
            if len(parts) >= 6:
                if delimiter != ";":
                    segments = operand.split(";")
                else:
                    segments = [parts[3 * i] + delimiter + parts[3 * i + 1] + delimiter + parts[3 * i + 2] for i in range(len(parts) // 3)]

            transform = ALPHA
            tainted = False

            for segment in segments:
                parts = segment.strip().split(delimiter)
                if len(parts) < 3:
                    continue

                pattern = parts[1]
                replacement = preprocess(parts[2])
                replacement = escape_literal_for_regular_type(replacement)
                replacement = replacement.replace("\\\\\\\\t", "\t")
                if "\\\\1" in replacement:
                    transform = ConstantTransform(RegularType(".*"))
                    continue
                if "\\\\" in replacement:
                    tainted = True

                if pattern == "^":
                    if replacement:
                        transform = ConcatenateTransform(ConstantTransform(RegularType(replacement, tainted=False)), transform)
                    continue
                if pattern == "\\$" or pattern == "$":
                    if replacement:
                        transform = ConcatenateTransform(transform, ConstantTransform(RegularType(replacement, tainted=False)))
                    continue

                pattern = pattern.replace("\\\\", "\\")
                pattern = preprocess(pattern)
                match = re.search(r"(\\+)$", pattern)
                if match and (len(match.group(1)) % 2 == 1):
                    pattern = pattern + delimiter

                transform = TranslateMatchTransform(
                    transform,
                    pattern,
                    replacement,
                    global_match=operand[-1] == "g",
                    mode=mode,
                )

            if tainted:
                transform = TaintTransform(transform, True)
            return PolymorphicCommandType(transform, self_contained=True)
        except Exception as error:
            if isinstance(error, ToolError):
                raise
            logging.debug("Falling back to passthrough sed command type for operand %r: %s", operand, error, exc_info=True)
            return PolymorphicCommandType(TaintTransform(ALPHA, True), self_contained=False)
        
def preprocess(string: str) -> str:
    if len(string) > 1:
        if string[-2] != "\\":
            if (string.startswith("'") and string.endswith("'")) or (string.startswith('"') and string.endswith('"')):
                string = string[1:-1]
    return string

def escape_literal_for_regular_type(string: str) -> str:
    return (
        re.escape(string)
        .replace("\\$", "[$]")
        .replace("\\{", "[{]")
        .replace("\\}", "[}]")
    )

def refine_log(s: str) -> str:
    if s == "":
        return "\"\""
    return s
