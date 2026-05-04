from stream.command_signature import CommandSignature, InferenceResult
from stream.regular_type import RegularType


class TeeSignature(CommandSignature):
    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        if previous_output_type.is_empty_string():
            return InferenceResult(RegularType(".*"), None, False)
        return super().output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
