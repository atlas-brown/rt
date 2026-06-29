import re
from stream.command_signature import CommandSignature
from stream.command_type import PolymorphicCommandType
from stream.transformation_ast import ALPHA, ComplementTransform, ConcatenateTransform, ConstantTransform, IntersectionTransform, LineExtractTransform, TaintTransform

from stream.regular_type import RegularType
from stream.tool_error import ToolError

class GrepSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def _normalized_operands(parsed_command_invocation):
        operands = [operand.name for operand in parsed_command_invocation.operand_list]
        if operands and operands[0] == "--":
            return operands[1:], True
        return operands, False

    @staticmethod
    def _contains_shell_expansion(pattern: str) -> bool:
        return re.search(r'(\$\{.*?\}|\$[a-zA-Z_][a-zA-Z0-9_]*|\$\()', pattern) is not None

    @staticmethod
    def _patterns_from_e_flags(flag_args: dict[str, list[str]], operands: list[str]) -> list[str]:
        patterns = list(flag_args.get("-e", []))
        if not patterns and operands:
            patterns = [operands[0]]
        return patterns

    @classmethod
    def _parsed_flags_and_operands(cls, parsed_command_invocation):
        operands, has_double_dash = cls._normalized_operands(parsed_command_invocation)
        operands = list(operands)
        flags = set()
        flag_args: dict[str, list[str]] = {}

        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            arg = flag.get_arg() if hasattr(flag, "get_arg") else None

            if name == "-f" and arg and arg.startswith("-") and len(arg) > 1 and operands:
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

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations):
        input_type, no_input_type = super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type
    
        parsed_flags, _, operands, has_double_dash = self._parsed_flags_and_operands(parsed_command_invocation)

        if len(operands) > 1 or (len(operands) == 1 and "-e" in parsed_flags):
            return RegularType(""), None

        if "-e" in parsed_flags or "-c" in parsed_flags or "-f" in parsed_flags:
            return input_type, no_input_type

        if "-n" in parsed_flags:
            return input_type, no_input_type
        if not operands:
            return input_type, no_input_type
        if "-e" not in parsed_flags:
            pattern = operands[0]
            if pattern.startswith("-") and not has_double_dash:
                raise ToolError("Pattern cannot start with '-'")
            if self._contains_shell_expansion(pattern):
                return input_type, None
            pattern = pattern.replace("\\\\", "\\")
            pattern = pattern.replace("\\\\|", "\\|")
            if "-F" in parsed_flags:
                pattern = re.escape(pattern)
        
        mode = "extended" if "-E" in parsed_flags else "basic"
        no_input_type = RegularType(pattern, mode)
        original_no_input_type = RegularType(pattern, mode)

        if "-o" not in parsed_flags:
            if not original_no_input_type.has_start_anchor:
                no_input_type = RegularType(".*") + no_input_type
            if not original_no_input_type.has_end_anchor:
                no_input_type = no_input_type + RegularType(".*")

        no_input_type = no_input_type.without_anchors()
        no_input_type.tainted = False

        if "-v" not in parsed_flags:
            return input_type, no_input_type
        else:
            return input_type, ~no_input_type

            
    def construct_command_type(self, parsed_command_invocation, env_annotations):
        self_contained = True
        source = ALPHA
        flags, flag_args, normalized_operands, has_double_dash = self._parsed_flags_and_operands(parsed_command_invocation)

        if len(normalized_operands) > 1 or (len(normalized_operands) == 1 and ("-e" in flags or "-f" in flags)):
            file_type = super().get_file_name(parsed_command_invocation, env_annotations)
            if file_type.tainted:
                self_contained = False
            source = ConstantTransform(file_type)

        mode = "extended" if "-E" in flags else "basic"

        if "-f" in flags and "-o" not in flags:
            if "-c" in flags:
                return PolymorphicCommandType(ConstantTransform(RegularType("[0-9]+")), self_contained=self_contained)
            return PolymorphicCommandType(source, self_contained=self_contained)

        if "-e" in flags:
            patterns = self._patterns_from_e_flags(flag_args, normalized_operands)
            if not patterns:
                return PolymorphicCommandType(TaintTransform(source, True), self_contained=False)

            pattern_type = RegularType(patterns[0], mode, tainted=False)
            original_pattern_type = RegularType(patterns[0], mode, tainted=False)
            for arg in patterns[1:]:
                arg = arg.replace("\\\\", "\\")
                pattern_type = pattern_type | RegularType(arg, mode, tainted=False)
                original_pattern_type = original_pattern_type | RegularType(arg, mode, tainted=False)
        else:
            if len(normalized_operands) == 0 and "-f" not in flags:
                raise ToolError("No pattern provided for grep")
            if len(normalized_operands) == 0:
                return PolymorphicCommandType(TaintTransform(source, True), self_contained=False)
            pattern = normalized_operands[0]
            if pattern.startswith("--") and not has_double_dash:
                raise ToolError("Pattern cannot start with '--'")
            pattern = pattern.replace("\\\\", "\\")
            if "-F" in flags:
                pattern = re.escape(pattern)
            pattern_type = RegularType(pattern, mode, tainted=False)
            original_pattern_type = RegularType(pattern, mode, tainted=False)

        if "-c" in flags:
            return PolymorphicCommandType(ConstantTransform(RegularType("[0-9]+")), self_contained=self_contained)

        if "-o" not in flags:
            if not original_pattern_type.has_start_anchor:
                pattern_type = RegularType(".*", tainted=False) + pattern_type
            if not original_pattern_type.has_end_anchor:
                pattern_type = pattern_type + RegularType(".*", tainted=False)
            pattern_type = pattern_type.without_anchors()
            pattern_node = ConstantTransform(pattern_type)
            transform = IntersectionTransform(source, pattern_node)
        else:
            if not original_pattern_type.has_start_anchor and not original_pattern_type.has_end_anchor:
                pattern_type.tainted = True
                return PolymorphicCommandType(ConstantTransform(pattern_type), self_contained=self_contained)
            pattern_type = pattern_type.without_anchors()
            transform = IntersectionTransform(source, ConstantTransform(pattern_type))

        if "-w" in flags:
            word_pattern = RegularType("(.*[^a-zA-Z0-9_])?", tainted=False) + pattern_type + RegularType("([^a-zA-Z0-9_].*)?", tainted=False)
            pattern_type = word_pattern
            transform = IntersectionTransform(source, ConstantTransform(word_pattern))
        if "-v" in flags:
            transform = IntersectionTransform(source, ComplementTransform(ConstantTransform(pattern_type)))
        if "-n" in flags:
            transform = ConcatenateTransform(ConstantTransform(RegularType("[0-9]+:", tainted=False)), transform)
        if "-P" in flags or "-m" in flags:
            transform = TaintTransform(transform, True)

        return PolymorphicCommandType(transform, self_contained=self_contained)
