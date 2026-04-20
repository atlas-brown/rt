import re
import traceback
from stream.command_signature import CommandSignature, InferenceResult
from pash_annotations.datatypes.BasicDatatypes import Operand

from stream.regular_type import RegularType, ends_with_end_anchor, remove_anchors, starts_with_start_anchor
from stream.tool_error import ToolError
from functools import reduce

from stream.transducer import product_fst_automaton, stream_based_filter_FST
from stream.user_annotation import AnnotationType
# from stream.utils.logger import get_logger
from stream.regex_parser import is_pure_string_for_ast

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

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations):
        input_type, no_input_type = super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type
    
        parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
        operands, has_double_dash = self._normalized_operands(parsed_command_invocation)

        if len(operands) > 1 or (len(operands) == 1 and "-e" in parsed_flags):
            return RegularType(""), None

        # FIXME: consider -e
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
            # FIXME not completely correct, for example pattern is a|^b
            if not starts_with_start_anchor(original_no_input_type):
                no_input_type = RegularType(".*") + no_input_type
            if not ends_with_end_anchor(original_no_input_type):
                no_input_type = no_input_type + RegularType(".*")

        no_input_type = remove_anchors(no_input_type)
        no_input_type.tainted = False

        if "-v" not in parsed_flags:
            return input_type, no_input_type
        else:
            return input_type, ~no_input_type

            

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        # Classify the last detailed command invocation as supported
        # get_logger().classify_last_invocation_as_supported()
        supported_flags = set(["-e", "-o", "-i", "-v", "-x", "-n", "-G", "-E", "-F", "-w", "-A", "-B", "-C", "-P"])
        
        # Record command pattern based on flag combination
        # flag_pattern = get_logger().get_flag_pattern_from_invocation(parsed_command_invocation)
        # get_logger().add_command_pattern_log("grep", flag_pattern)
        
        self_contained = True
        normalized_operands, has_double_dash = self._normalized_operands(parsed_command_invocation)
        if len(normalized_operands) > 1 or (len(normalized_operands) == 1 and "-e" in parsed_command_invocation.flag_option_list):
            previous_output_type = super().get_file_name(parsed_command_invocation, env_annotations)
            if previous_output_type.tainted:
                self_contained = False
        lose_precision = False

        flags = set()
        flag_args : dict[str, list[str]] = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, 'get_arg') and flag.get_arg():
                if name not in flag_args:
                    flag_args[name] = []
                flag_args[name].append(flag.get_arg())

        mode = "extended" if "-E" in flags else "basic"

        if "-e" in flags:
            patterns = self._patterns_from_e_flags(flag_args, normalized_operands)
            if not patterns:
                previous_output_type.tainted = True
                return InferenceResult(previous_output_type, lambda x: x, False)

            arg_count = len(parsed_command_invocation.operand_list) + 1
            pattern_type = RegularType(patterns[0], mode)
            pattern_type_str = pattern_type.pattern
            original_pattern_type = RegularType(patterns[0], mode)
            for arg in patterns[1:]:
                arg = arg.replace("\\\\", "\\")
                # get_logger().add_regex_log(arg)
                pattern_type = pattern_type | RegularType(arg, mode)
                original_pattern_type = original_pattern_type | RegularType(arg, mode)
                pattern_type_str = f"({pattern_type_str})|({arg})"
            
            # Update pattern analysis for first -e pattern
            if patterns:
                first_pattern = patterns[0]
                first_pattern_type = RegularType(first_pattern, mode)
                is_pure = is_pure_string_for_ast(first_pattern_type.ast) if hasattr(first_pattern_type, 'ast') else False
                # get_logger().update_last_pattern_analysis(
                #     pattern=first_pattern,
                #     ast_repr=str(first_pattern_type.ast) if hasattr(first_pattern_type, 'ast') else "N/A",
                #     is_pure_string=is_pure
                # )
            else:
                # get_logger().remove_last_pattern_analysis()
                pass
            
        else:
            if len(normalized_operands) == 0 and "-f" not in flags:
                # get_logger().remove_last_pattern_analysis()
                raise ToolError("No pattern provided for grep")
            if len(normalized_operands) == 0:
                previous_output_type.tainted = True
                return InferenceResult(previous_output_type, lambda x: x, False)
            pattern = normalized_operands[0]
            if pattern.startswith("--") and not has_double_dash:
                raise ToolError("Pattern cannot start with '--'")
            pattern = pattern.replace("\\\\", "\\")
            if "-F" in flags:
                pattern = re.escape(pattern)
            # get_logger().add_regex_log(pattern)
            pattern_type = RegularType(pattern, mode)
            pattern_type_str = pattern_type.pattern
            original_pattern_type = RegularType(pattern, mode)
            arg_count = len(parsed_command_invocation.operand_list)
            
            # Update pattern analysis
            is_pure = is_pure_string_for_ast(pattern_type.ast) if hasattr(pattern_type, 'ast') else False
            # get_logger().update_last_pattern_analysis(
            #     pattern=pattern,
            #     ast_repr=str(pattern_type.ast) if hasattr(pattern_type, 'ast') else "N/A",
            #     is_pure_string=is_pure
            # )

        # if flags.issubset(supported_flags):
        #     get_logger().classify_last_invocation_as_supported()
        # else:
        #     get_logger().classify_last_invocation_as_unsupported()

        if "-c" in flags:
            # NOTE(logger-state): output_type/precision stored for downstream type summaries.
            # get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = True
            # get_logger().get_latest_record()["command_list"][-1]["output_type"] = "[0-9]+"
            return InferenceResult(RegularType("[0-9]+"), lambda x: previous_output_type.get_shortest_example(), self_contained)

        # FIXME: -o processing is wrong!
        if "-o" not in flags:
            # FIXME not completely correct, for example pattern is a|^b
            if not starts_with_start_anchor(original_pattern_type):
                pattern_type = RegularType(".*") + pattern_type
                pattern_type_str = ".*" + pattern_type_str
            if not ends_with_end_anchor(original_pattern_type):
                pattern_type = pattern_type + RegularType(".*")
                pattern_type_str = pattern_type_str + ".*"

        else:
            # FIXME
            if not starts_with_start_anchor(original_pattern_type) and not ends_with_end_anchor(original_pattern_type):
                pattern_type.tainted = True
                lose_precision = True
                # NOTE(logger-state): output_type/precision stored for downstream type summaries.
                # get_logger().get_latest_record()["command_list"][-1]["output_type"] = pattern_type_str
                # get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = True
                return InferenceResult(pattern_type, lambda x: x, self_contained)
            else:
                pattern_type = remove_anchors(pattern_type)
        
        # FIXME not completely correct, for example pattern is a|^b
        pattern_type = remove_anchors(pattern_type)
        
        if "-w" in flags:
            pattern_type = RegularType("(.*[^a-zA-Z0-9_])?") + pattern_type + RegularType("([^a-zA-Z0-9_].*)?")
            pattern_type_str = "(.*[^a-zA-Z0-9_])?" + pattern_type_str + "([^a-zA-Z0-9_].*)?"
        if "-v" in flags:
            pattern_type = ~pattern_type
            pattern_type_str = "(~(" + pattern_type_str + "))"
        pattern_type = previous_output_type & pattern_type
        if previous_output_type.repr_mode == "stream":
            fst = stream_based_filter_FST(pattern_type.nfa)
            pattern_type = RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa), repr_mode="stream", tainted=False)
            
        current_type_str = f"α&{pattern_type_str}"

        if "-n" in flags:
            current_type_str = f"[0-9]+:({current_type_str})"
            pattern_type = RegularType("[0-9]+:") + pattern_type
        if "-P" in flags or "-m" in flags:
            pattern_type.tainted = True
            lose_precision = True
        else:   
            pattern_type.tainted = previous_output_type.tainted
        # NOTE(logger-state): output_type/precision stored for downstream type summaries.
        # get_logger().get_latest_record()["command_list"][-1]["output_type"] = current_type_str
        # get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = lose_precision
        return InferenceResult(pattern_type, lambda x: x, self_contained)
        
