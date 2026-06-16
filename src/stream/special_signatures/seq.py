import re
from stream.command_signature import CommandSignature
from stream.command_type import PolymorphicCommandType
from stream.regular_type import RegularType
from stream.transformation_ast import ConstantTransform
from stream.tool_error import ToolError

class SeqSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def construct_command_type(self, parsed_command_invocation, env_annotations):
        operands = super().get_operands(parsed_command_invocation)
        if len(operands) == 0:
            raise ToolError("No operand provided for seq")
        line_type = None
        if len(operands) == 1 and operands[0].isdigit():
            if int(operands[0]) <= 0:
                line_type = RegularType("")
            else:
                line_type = RegularType("[0-9]+")
        if len(operands) == 2 and operands[0].isdigit():
            if int(operands[0]) < 0:
                line_type = RegularType("-?[0-9]+")
            else:
                line_type = RegularType("[0-9]+")

        flags = set()
        flag_args = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, "get_arg") and flag.get_arg():
                flag_args[name] = flag.get_arg()

        delimiter = "\n"
        if "-s" in flags:
            delimiter = f"{flag_args['-s']}"

        while (delimiter[0] == "(" and delimiter[-1] == ")") or (delimiter[0] == "[" and delimiter[-1] == "]") or (delimiter[0] == "'" and delimiter[-1] == "'") or (delimiter[0] == '"' and delimiter[-1] == '"'):
            delimiter = delimiter[1:-1]
        delimiter = delimiter[-1]

        if delimiter == "\n" and line_type is not None:
            return PolymorphicCommandType(ConstantTransform(line_type), self_contained=True)
        if delimiter != "\n" and line_type is not None:
            out = line_type + (RegularType(f"{re.escape(delimiter)}") + line_type).kleene_star()
            return PolymorphicCommandType(ConstantTransform(out), self_contained=True)

        return super().construct_command_type(parsed_command_invocation, env_annotations)
