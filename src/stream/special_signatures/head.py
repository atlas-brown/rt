import re
from stream.command_signature import CommandSignature
from stream.command_type import PolymorphicCommandType
from stream.regular_type import RegularType
from stream.transformation_ast import ALPHA, ConstantTransform, HeadLinesTransform
from stream.tool_error import ToolError

class HeadSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def construct_command_type(self, parsed_command_invocation, env_annotations):
        source = ALPHA
        self_contained = True
        if len(parsed_command_invocation.operand_list) > 0:
            file_type = super().get_file_name(parsed_command_invocation, env_annotations)
            if file_type.tainted:
                self_contained = False
            source = ConstantTransform(file_type)

        flags = set()
        flag_args : dict[str, list[str]] = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, "get_arg") and flag.get_arg():
                if name not in flag_args:
                    flag_args[name] = []
                flag_args[name].append(flag.get_arg())
        if "-n" in flags:
            try:
                return PolymorphicCommandType(HeadLinesTransform(source, int(flag_args["-n"][0])), self_contained=self_contained)
            except Exception:
                return PolymorphicCommandType(source, self_contained=self_contained, output_tainted=True)
        return super().construct_command_type(parsed_command_invocation, env_annotations)
