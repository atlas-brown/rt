import re
from stream.command_signature import CommandSignature
from stream.command_type import PolymorphicCommandType
from stream.regular_type import RegularType
from stream.transformation_ast import ALPHA, ConstantTransform, ReverseTransform
from stream.tool_error import ToolError

class RevSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_input_type(self, parsed_command_invocation, heuristic_rules, env_annotations):
        if len(parsed_command_invocation.operand_list) > 0 and "no_ignored_input" in heuristic_rules:
            return RegularType(""), None
        return super().get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)

    def construct_command_type(self, parsed_command_invocation, env_annotations):
        source = ALPHA
        self_contained = True
        if len(parsed_command_invocation.operand_list) > 0:
            file_type = super().get_file_name(parsed_command_invocation, env_annotations)
            if file_type.tainted:
                self_contained = False
            source = ConstantTransform(file_type)
        return PolymorphicCommandType(ReverseTransform(source), self_contained=self_contained)
