from stream.command_signature import CommandSignature
from pash_annotations.datatypes.BasicDatatypes import Operand

from stream.regular_type import RegularType, ends_with_end_anchor, remove_anchors, starts_with_start_anchor
from stream.tool_error import ToolError
from functools import reduce

from stream.user_annotation import AnnotationType

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
        if "-e" in parsed_flags:
            return input_type, no_input_type

        if "-n" in parsed_flags:
            return input_type, no_input_type
        if "-e" not in parsed_flags:
            pattern = parsed_command_invocation.operand_list[0].name
            pattern = pattern.replace("\\\\", "\\")
        
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

        if "-v" not in parsed_flags:
            return input_type, no_input_type
        else:
            return input_type, ~no_input_type

            

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        if len(parsed_command_invocation.operand_list) > 1 or (len(parsed_command_invocation.operand_list) == 1 and "-e" in parsed_command_invocation.flag_option_list):
            previous_output_type = super().get_file_name(parsed_command_invocation, env_annotations)


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
                pattern_type = pattern_type | RegularType(arg, mode)
                original_pattern_type = original_pattern_type | RegularType(arg, mode)
            
            
        else:
            if len(parsed_command_invocation.operand_list) == 0:
                raise ToolError("No pattern provided for grep")
            pattern = parsed_command_invocation.operand_list[0].name
            pattern = pattern.replace("\\\\", "\\")
            pattern_type = RegularType(pattern, mode)
            original_pattern_type = RegularType(pattern, mode)
            arg_count = len(parsed_command_invocation.operand_list)


        # FIXME: -o processing is wrong!
        if "-o" not in flags:
            # FIXME not completely correct, for example pattern is a|^b
            if not starts_with_start_anchor(original_pattern_type):
                pattern_type = RegularType(".*") + pattern_type
            if not ends_with_end_anchor(original_pattern_type):
                pattern_type = pattern_type + RegularType(".*")
        
        # FIXME not completely correct, for example pattern is a|^b
        pattern_type = remove_anchors(pattern_type)
        
        if "-w" in flags:
            pattern_type = RegularType("(.*[^a-zA-Z0-9_])?") + pattern_type + RegularType("([^a-zA-Z0-9_].*)?")

        if "-v" in flags:
            pattern_type = ~pattern_type

        pattern_type = previous_output_type & pattern_type

        if "-n" in flags:
            pattern_type = RegularType("[0-9]+:") + pattern_type

        return pattern_type
        
