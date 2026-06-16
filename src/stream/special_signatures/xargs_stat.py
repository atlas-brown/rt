from stream.command_signature import CommandSignature
from stream.command_type import PolymorphicCommandType
from stream.regular_type import RegularType
from stream.transformation_ast import ConstantTransform

class XargsStatSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def construct_command_type(self, parsed_command_invocation, env_annotations):
        operands = super().get_operands(parsed_command_invocation)
        for operand, next_operand in zip(operands, operands[1:]):
            if operand == "-c":
                if next_operand == "%Y":
                    return PolymorphicCommandType(ConstantTransform(RegularType("[0-9]+")), self_contained=False)
                if next_operand in {"%y", "%x"}:
                    return PolymorphicCommandType(ConstantTransform(RegularType(".*")), self_contained=False)
        command_type = super().construct_command_type(parsed_command_invocation, env_annotations)
        command_type.self_contained = False
        return command_type
