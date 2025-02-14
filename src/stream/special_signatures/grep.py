from command_signature import CommandSignature
from pash_annotations.datatypes.BasicDatatypes import Operand

from stream.regular_type import RegularType, concat, complement, ends_with_end_anchor, intersect, remove_anchors, starts_with_start_anchor, union
from stream.tool_error import ToolError
from functools import reduce

class GrepSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_input_type(self, parsed_command_invocation, heuristic_rules):
        input_type, no_input_type = super().get_input_type(parsed_command_invocation, heuristic_rules)
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type
    
        
        # FIXME: consider -e
        if len(parsed_command_invocation.operand_list) != 1:
            return input_type, no_input_type
    
        parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))

        if "-n" in parsed_flags:
            return input_type, no_input_type
        
        pattern = parsed_command_invocation.operand_list[0].name
        
        mode = "extended" if "-E" in parsed_flags else "basic"
        pattern_type = RegularType(pattern, mode)

        # FIXME: consider ^ and $, for example, grep input is .*a and pattern is ^a, then it is valid
        pattern_type = remove_anchors(pattern_type)

        # FIXME: consider -o
        no_input_type = concat([RegularType(".*"), pattern_type, RegularType(".*")])

        if "-v" not in parsed_flags:
            return input_type, no_input_type
        else:
            return input_type, complement(no_input_type)

            

    def output_type_inference(self, previous_output_type, parsed_command_invocation):
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
            types = []
            arg_count = len(parsed_command_invocation.operand_list) + 1
            for arg in flag_args["-e"]:
                types.append(RegularType(arg, mode))
            pattern_type = reduce(lambda acc, reg: union([acc, reg]), types)
            
            
        else:
            if len(parsed_command_invocation.operand_list) == 0:
                raise ToolError("No pattern provided for grep")
            pattern = parsed_command_invocation.operand_list[0].name
            pattern_type = RegularType(pattern, mode)
            arg_count = len(parsed_command_invocation.operand_list)


        # FIXME: -o processing is wrong!
        if "-o" not in flags:
            # FIXME not completely correct, for example pattern is a|^b
            if not starts_with_start_anchor(pattern_type):
                pattern_type = concat([RegularType(".*"), pattern_type])
            if not ends_with_end_anchor(pattern_type):
                pattern_type = concat([pattern_type, RegularType(".*")])
        
        # FIXME not completely correct, for example pattern is a|^b
        pattern_type = remove_anchors(pattern_type)
        
        if "-w" in flags:
            pattern_type = concat([RegularType("(.*[^a-zA-Z0-9_])?"), pattern_type, RegularType("([^a-zA-Z0-9_].*)?")])

        if "-v" in flags:
            pattern_type = complement(pattern_type)

        if arg_count == 1:
            pattern_type = intersect(previous_output_type, pattern_type)

        if "-n" in flags:
            pattern_type = concat([RegularType("[0-9]+:"), pattern_type])

        return pattern_type
        
