import traceback
from stream.command_signature import CommandSignature, InferenceResult
from pash_annotations.datatypes.BasicDatatypes import Operand

from stream.regular_type import RegularType, ends_with_end_anchor, remove_anchors, starts_with_start_anchor
from stream.tool_error import ToolError
from functools import reduce

from stream.user_annotation import AnnotationType
from stream.utils.logger import get_logger

class GrepSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations):
        input_type, no_input_type = super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type
    
        parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))

        if len(parsed_command_invocation.operand_list) > 1 or (len(parsed_command_invocation.operand_list) == 1 and "-e" in parsed_flags):
            return RegularType(""), None

        # FIXME: consider -e
        if "-e" in parsed_flags or "-c" in parsed_flags:
            return input_type, no_input_type

        if "-n" in parsed_flags:
            return input_type, no_input_type
        if "-e" not in parsed_flags:
            pattern = parsed_command_invocation.operand_list[0].name
            if pattern.startswith("-"):
                raise ToolError("Pattern cannot start with '-'")
            pattern = pattern.replace("\\\\", "\\")
            pattern = pattern.replace("\\\\|", "\\|")
        
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
        self_contained = True
        if len(parsed_command_invocation.operand_list) > 1 or (len(parsed_command_invocation.operand_list) == 1 and "-e" in parsed_command_invocation.flag_option_list):
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
            arg_count = len(parsed_command_invocation.operand_list) + 1
            pattern_type = RegularType(flag_args["-e"][0], mode)
            original_pattern_type = RegularType(flag_args["-e"][0], mode)
            for arg in flag_args["-e"][1:]:
                arg = arg.replace("\\\\", "\\")
                get_logger().add_regex_log(arg)
                pattern_type = pattern_type | RegularType(arg, mode)
                original_pattern_type = original_pattern_type | RegularType(arg, mode)
            
            
        else:
            if len(parsed_command_invocation.operand_list) == 0 and "-f" not in flags:
                raise ToolError("No pattern provided for grep")
            pattern = parsed_command_invocation.operand_list[0].name
            pattern = pattern.replace("\\\\", "\\")
            get_logger().add_regex_log(pattern)
            pattern_type = RegularType(pattern, mode)
            pattern_type_str = pattern_type.pattern
            original_pattern_type = RegularType(pattern, mode)
            arg_count = len(parsed_command_invocation.operand_list)

        if "-c" in flags:
            get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = True
            get_logger().get_latest_record()["command_list"][-1]["output_type"] = "[0-9]+"
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
                get_logger().get_latest_record()["command_list"][-1]["output_type"] = pattern_type_str
                get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = True
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
        current_type_str = f"α&{pattern_type_str}"

        if "-n" in flags:
            current_type_str = f"[0-9]+:({current_type_str})"
            pattern_type = RegularType("[0-9]+:") + pattern_type
        if "-P" in flags or "-m" in flags:
            pattern_type.tainted = True
            lose_precision = True
        else:   
            pattern_type.tainted = previous_output_type.tainted
        get_logger().get_latest_record()["command_list"][-1]["output_type"] = current_type_str
        get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = lose_precision
        return InferenceResult(pattern_type, lambda x: x, self_contained)
        
