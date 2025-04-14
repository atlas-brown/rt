import re
from stream.command_signature import CommandSignature
from stream.regular_type import RegularType
from stream.tool_error import ToolError
from stream.regex_parser import convert_to_pure_string, is_pure_string
from stream.transducer import first_regex_replacement_FST, first_replacement_FST, global_regex_replacement_FST, global_replacement_FST, product_fst_automaton, start_regex_replacement_FST

class SedSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations):
        input_type, no_input_type = super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)
        if "no_meaningless_command" not in heuristic_rules:
            return input_type, no_input_type
        
        operands = super().get_operands(parsed_command_invocation)
        # FIXME: sed -e, sed needs extra pash annotation
        if len(operands) == 0:
            raise ToolError("No operand provided for sed")
        operand = operands[0]
        if not operand.startswith("s"):
            return input_type, no_input_type
        delimiter = operand[1]
        parts = operand.split(delimiter)
        if len(parts) < 3:
            return input_type, no_input_type
        if parts[1] == '^' or parts[1] == '\\$':
            return input_type, no_input_type
        # Fixme: handle start and end anchors
        if parts[0] == 's':
            parts[1] = parts[1].replace("\\\\", "\\")
            parts[1] = preprocess(parts[1])
            # FIXME: provisional solution for sed s/\///g : if ends with an odd number of backslashes, then add '/' to the end
            match = re.search(r'(\\+)$', parts[1])
            if match and (len(match.group(1)) % 2 == 1):
                parts[1] = parts[1] + delimiter
            if parts[1].endswith("$"):
                parts[1] = parts[1][:-2]
            no_input_type = ~(RegularType(".*") + RegularType(parts[1]) + RegularType(".*"))
            no_input_type.tainted = False
            return input_type, no_input_type
        return input_type, no_input_type


    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        tainted = previous_output_type.tainted
        operands = super().get_operands(parsed_command_invocation)
        parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
        if len(operands) == 0:
            raise ToolError("No operand provided for sed")
        operand = operands[0]
        if operand == "d":
            return RegularType("")
        if operand[-1] == "d" and operand[:-1].isdigit():
            return previous_output_type
        if not operand.startswith("s"):
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        delimiter = operand[1]
        parts = operand.split(delimiter)
        segments = [operand]
        if len(parts) < 3:
            return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        if len(parts) >= 6:
            if delimiter != ";":
                segments = operand.split(";")
            else:
                segments = [parts[3 * i] + delimiter + parts[3 * i + 1] + delimiter + parts[3 * i + 2] for i in range(len(parts) // 3)]
        
        for segment in segments:
            parts = segment.strip().split(delimiter)
            if parts[1] == '^':
                parts[2] = preprocess(parts[2])
                parts[2] = re.escape(parts[2])
                previous_output_type = RegularType(parts[2]) + previous_output_type
            # FIXME: figure out the difference between $ and \\$
            elif parts[1] == '\\$' or parts[1] == "$":
                parts[2] = preprocess(parts[2])
                parts[2] = re.escape(parts[2])
                previous_output_type = previous_output_type + RegularType(parts[2])
            else:
                parts[1] = parts[1].replace("\\\\", "\\")
                parts[1] = preprocess(parts[1])
                parts[2] = preprocess(parts[2])
                parts[2] = re.escape(parts[2])
                # FIXME: provisional solution for sed s/\///g : if ends with an odd number of backslashes, then add '/' to the end
                match = re.search(r'(\\+)$', parts[1])
                if match and (len(match.group(1)) % 2 == 1):
                    parts[1] = parts[1] + delimiter
                
                mode = "extended" if "-E" in parsed_flags else "basic"
                if is_pure_string(parts[1], mode):
                    s1 = convert_to_pure_string(parts[1], mode)
                    if operand[-1] == "g":
                        fst = global_replacement_FST(s1, parts[2])
                    else:
                        fst = first_replacement_FST(s1, parts[2])
                    nfa = product_fst_automaton(fst, previous_output_type.nfa)
                    previous_output_type = RegularType(automaton=nfa)
                else:
                    if parts[1].startswith("^") and parts[1].endswith("$"):
                        parts[1] = parts[1][1:-1]
                        if parts[1].endswith("\\"):
                            parts[1] = parts[1][:-1]
                        fst = start_regex_replacement_FST(RegularType(".*").nfa, parts[2])
                        input_typ1 = previous_output_type & RegularType(parts[1])
                        input_typ2 = previous_output_type - RegularType(parts[1])
                        output_automaton = product_fst_automaton(fst, input_typ1.nfa)
                        previous_output_type = RegularType(automaton=output_automaton) | input_typ2
                    elif parts[1].startswith("^"):
                        automata = RegularType(parts[1], mode).nfa
                        fst = start_regex_replacement_FST(automata, parts[2])
                        nfa = product_fst_automaton(fst, previous_output_type.nfa)
                        previous_output_type = RegularType(automaton=nfa)
                    elif parts[1].endswith("$"):
                        parts[1] = parts[1][:-2]
                        automata = RegularType(parts[1], mode).reverse().nfa
                        fst = start_regex_replacement_FST(automata, parts[2][::-1])
                        nfa = product_fst_automaton(fst, previous_output_type.reverse().nfa)
                        previous_output_type = RegularType(automaton=nfa).reverse()
                    elif operand[-1] == "g":
                        automata = RegularType(parts[1], mode).nfa
                        fst = global_regex_replacement_FST(automata, parts[2])
                        nfa = product_fst_automaton(fst, previous_output_type.nfa)
                        previous_output_type = RegularType(automaton=nfa)
                    else:
                        automata = RegularType(parts[1], mode).nfa
                        fst = first_regex_replacement_FST(automata, parts[2])
                        nfa = product_fst_automaton(fst, previous_output_type.nfa)
                        previous_output_type = RegularType(automaton=nfa)
                    
                # return previous_output_type & ~(RegularType(".*") + RegularType(parts[1]) + RegularType(".*"))
        previous_output_type.tainted = tainted
        return previous_output_type
        return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        
def preprocess(string: str) -> str:
    if len(string) > 1:
        if string[-2] != "\\":
            if (string.startswith("'") and string.endswith("'")) or (string.startswith('"') and string.endswith('"')):
                string = string[1:-1]
    return string