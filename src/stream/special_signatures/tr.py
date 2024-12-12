import re
from command_signature import CommandSignature
from stream.regular_type import RegularType
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from stream.tool_error import ToolError

class TrSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def output_type_inference(self, previous_output_type: RegularType, parsed_command_invocation: CommandInvocationInitial) -> RegularType:
        return super().output_type_inference(previous_output_type, parsed_command_invocation)