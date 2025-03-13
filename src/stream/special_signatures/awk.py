import re
from command_signature import CommandSignature
from stream.regular_type import RegularType
from stream.tool_error import ToolError
from stream.transducer import compression_FST, cut_field_FST, first_regex_replacement_FST, product_fst_automaton, translate_to_line_delimited_FST

class AwkSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        if len(parsed_command_invocation.operand_list) != 1:
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        operand = parsed_command_invocation.operand_list[0].name
        match = re.search(r'print\s+\$(\d+)', operand)
        if match is None:
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        try:
            column_number = int(match.group(1))
            fst1 = first_regex_replacement_FST(RegularType(" +").nfa, "")
            fst2 = compression_FST(" ")
            fst3 = cut_field_FST(" ", [column_number])
            nfa = product_fst_automaton(fst1, previous_output_type.nfa)
            nfa = product_fst_automaton(fst2, nfa)
            nfa = product_fst_automaton(fst3, nfa)
            return RegularType(automaton=nfa)
        except Exception:
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        
        