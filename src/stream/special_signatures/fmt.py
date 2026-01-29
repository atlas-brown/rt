import re
from stream.command_signature import CommandSignature
from stream.regular_type import RegularType
from stream.tool_error import ToolError
from stream.transducer import product_fst_automaton, translate_to_line_delimited_FST
from stream.utils.logger import get_logger

class FmtSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        # Classify the last detailed command invocation as supported
        # get_logger().classify_last_invocation_as_supported()
        
        # Record command pattern based on flag combination
        # flag_pattern = get_logger().get_flag_pattern_from_invocation(parsed_command_invocation)
        # get_logger().add_command_pattern_log("fmt", flag_pattern)
        
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
                # NOTE(logger-state): output_type/precision stored for downstream type summaries.
                # get_logger().get_latest_record()["command_list"][-1]["output_type"] = f"translate-match(α, \" \\t\", \\n, squeeze=True)"
                # get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = False
                return RegularType(automaton=product_fst_automaton(fst, previous_output_type.nfa)) & RegularType(".+")
            
        return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)

        
        
            



















