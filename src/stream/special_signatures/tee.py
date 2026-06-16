from stream.command_signature import CommandSignature
from stream.command_type import PolymorphicCommandType
from stream.regular_type import RegularType
from stream.transformation_ast import ALPHA, ConstantTransform, DefaultIfEmptyStringTransform


class TeeSignature(CommandSignature):
    def construct_command_type(self, parsed_command_invocation, env_annotations):
        transform = DefaultIfEmptyStringTransform(ALPHA, ConstantTransform(RegularType(".*")))
        return PolymorphicCommandType(transform, self_contained=False)
