import re
from stream.command_signature import CommandSignature
from stream.command_type import PolymorphicCommandType
from stream.regular_type import RegularType
from stream.transformation_ast import ALPHA, ConcatenateTransform, ConstantTransform, IntersectionTransform, TranslateCharsTransform
from stream.tool_error import ToolError

class FmtSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def construct_command_type(self, parsed_command_invocation, env_annotations):
        flags = set()
        flag_args = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, "get_arg") and flag.get_arg():
                flag_args[name] = flag.get_arg()

        if "-w" in flags:
            width = int(flag_args["-w"])
            if width == 1:
                base = IntersectionTransform(
                    TranslateCharsTransform(ALPHA, " \t", "\n", line_delimited=True),
                    ConstantTransform(RegularType(".+", tainted=False)),
                )
                transform = ConcatenateTransform(ConstantTransform(RegularType(" *", tainted=False)), base)
                return PolymorphicCommandType(transform, self_contained=True)

        return super().construct_command_type(parsed_command_invocation, env_annotations)
