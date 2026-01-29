from stream.command_signature import CommandSignature, InferenceResult
from stream.regular_type import RegularType
# from stream.utils.logger import get_logger

class XargsStatSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        # NOTE(logger-state): output_type/precision stored for downstream type summaries.
        # get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = True
        operands = super().get_operands(parsed_command_invocation)
        for operand, next_operand in zip(operands, operands[1:]):
            if operand == '-c':
                if next_operand == '%Y':
                    # stat -c %Y
                    # get_logger().get_latest_record()["command_list"][-1]["output_type"] = "[0-9]+"
                    return InferenceResult(RegularType("[0-9]+"), lambda x: previous_output_type.get_shortest_example(), False)
                elif next_operand == '%y':
                    # stat -c %y need to modify the regex
                    # get_logger().get_latest_record()["command_list"][-1]["output_type"] = ".*"
                    return InferenceResult(RegularType(".*"), lambda x: previous_output_type.get_shortest_example(), False)
                elif next_operand == '%x':
                    # stat -c %x need to modify the regex
                    # get_logger().get_latest_record()["command_list"][-1]["output_type"] = ".*"
                    return InferenceResult(RegularType(".*"), lambda x: previous_output_type.get_shortest_example(), False)
                
        inference_result = super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        if isinstance(inference_result, InferenceResult):
            inference_result.self_contained = False
        elif isinstance(inference_result, RegularType):
            inference_result = InferenceResult(inference_result, None, False)
        return inference_result
        
