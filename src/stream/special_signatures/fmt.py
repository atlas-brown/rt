import re
from stream.command_signature import CommandSignature
from stream.regular_type import RegularType
from stream.tool_error import ToolError
from stream.transducer import product_fst_automaton, translate_to_line_delimited_FST

class FmtSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        
        flags = set()
        flag_args = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, 'get_arg') and flag.get_arg():
                flag_args[name] = flag.get_arg()

        if "-w" in flags:
            width = int(flag_args["-w"])
            if width == 1:
                fst = translate_to_line_delimited_FST(" \t")
                base = RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa)) & RegularType(".+")
                # fmt -w1 preserves indentation for the first output line; allow optional leading whitespace.
                leading_spaces_concat_base = RegularType(" *") + base
                return leading_spaces_concat_base
            
        return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)

        
        
            



















