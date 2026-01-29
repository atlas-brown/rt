import re
from stream.command_signature import CommandSignature, InferenceResult
from stream.regular_type import RegularType
from stream.tool_error import ToolError
from stream.transducer import correct_cut_field_FST, cut_field_FST, head_FST, product_fst_automaton, tail_FST
# from stream.utils.logger import get_logger

class HeadSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        self_contained = True
        if len(parsed_command_invocation.operand_list) > 0:
            previous_output_type = super().get_file_name(parsed_command_invocation, env_annotations)
            if previous_output_type.tainted:
                self_contained = False
        # NOTE(logger-state): output_type/precision stored for downstream type summaries.
        # get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = True
        flags = set()
        flag_args : dict[str, list[str]] = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, 'get_arg') and flag.get_arg():
                if name not in flag_args:
                    flag_args[name] = []
                flag_args[name].append(flag.get_arg())
        if "-n" in flags:
            try:
                num_lines = int(flag_args["-n"][0])
                if num_lines <= 7:
                    output_type = RegularType(automaton=product_fst_automaton(head_FST("\n", num_lines), previous_output_type.to_full_stream_repr().nfa), repr_mode="stream", tainted=previous_output_type.tainted)
                else:
                    output_type = previous_output_type.to_line_based_repr()
                # output_type.possible_line_numbers = (num_lines, num_lines)
                # output_type.tainted = True
            except Exception as e:
                output_type = previous_output_type
                output_type.tainted = True
            # NOTE(logger-state): output_type/precision stored for downstream type summaries.
            # get_logger().get_latest_record()["command_list"][-1]["output_type"] = "α"
            return InferenceResult(output_type, lambda x: x, self_contained)
        return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        
        
