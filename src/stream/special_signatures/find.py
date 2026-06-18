from stream.command_signature import CommandSignature
from stream.command_type import PolymorphicCommandType, SimpleCommandType
from stream.regular_type import RegularType
from stream.transformation_ast import (
    ComposeTransform,
    ConstantTransform,
    SubtractionTransform,
)
from pash_annotations.datatypes.BasicDatatypes import Flag, Operand, Option
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
import re


class FindSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def construct_command_type(self, parsed_command_invocation, env_annotations):
        output_transform = self._construct_output_transform(parsed_command_invocation, env_annotations)
        return PolymorphicCommandType(output_transform, self_contained=False)

    def _construct_output_transform(self, parsed_command_invocation, env_annotations):
        operands = [operand.name for operand in parsed_command_invocation.operand_list]
        exec_command, exec_name = self._extract_exec_command(operands)
        if exec_command is None:
            return ConstantTransform(self._infer_find_output_type(operands))

        exec_command_type = self._lookup_command_type(exec_command, env_annotations)
        if exec_command_type is None:
            return ConstantTransform(RegularType(".+"))

        if isinstance(exec_command_type, SimpleCommandType):
            output_transform = ConstantTransform(exec_command_type.output_type)
        else:
            output_transform = ComposeTransform(
                exec_command_type.transformation,
                ConstantTransform(RegularType(".+")),
                normalize_input_to_line=exec_command_type.normalize_input_to_line,
                output_tainted=exec_command_type.output_tainted,
            )

        # Special case for 'ls' command: remove "total" line from output type.
        if exec_name == "ls":
            output_transform = SubtractionTransform(
                output_transform,
                ConstantTransform(RegularType("total .+")),
            )
        return output_transform

    def _infer_find_output_type(self, operands):
        output_type = RegularType(".+")
        if operands:
            search_path = operands[0]
            if not search_path.startswith('-'):
                name_pattern = None
                for i in range(len(operands) - 1):
                    if operands[i] == "-name" and i + 1 < len(operands):
                        name_pattern = operands[i + 1]
                        break

                if name_pattern and ('*' in name_pattern or '?' in name_pattern):
                    regex_pattern = re.escape(name_pattern).replace('\\*', '.*').replace('\\?', '.')
                    escaped_path = re.escape(search_path)
                    if search_path.endswith('/'):
                        output_type = RegularType(f"{escaped_path}.*{regex_pattern}")
                    else:
                        output_type = RegularType(f"{escaped_path}(/.*)?/{regex_pattern}")
                else:
                    escaped_path = re.escape(search_path)
                    if search_path.endswith('/'):
                        output_type = RegularType(f"{escaped_path}.*")
                    else:
                        output_type = RegularType(f"{escaped_path}(/.+)?")
        return output_type

    def _extract_exec_command(self, operands):
        for i in range(len(operands) - 3):
            if operands[i:i + 4] != ["-e", "-x", "-e", "-c"]:
                continue

            cmd_index = i + 4
            if cmd_index >= len(operands):
                return None, None

            cmd_name = operands[cmd_index]
            cmd_args = []
            j = cmd_index + 1
            while j < len(operands) and operands[j] not in {";", "+"}:
                if operands[j] != "{}":
                    cmd_args.append(operands[j])
                j += 1

            flag_option_list = []
            operand_list = []
            for arg in cmd_args:
                if arg.startswith('-'):
                    if '=' in arg:
                        option_name, option_arg = arg.split('=', 1)
                        flag_option_list.append(Option(option_name, option_arg))
                    else:
                        flag_option_list.append(Flag(arg))
                else:
                    operand_list.append(Operand(arg))

            return CommandInvocationInitial(cmd_name, flag_option_list, operand_list), cmd_name
        return None, None

    def _lookup_command_type(self, command_invocation, env_annotations):
        from stream.signature_loader import SignatureLoader
        loader = SignatureLoader.get_instance()

        signature = loader.find_signature(command_invocation)
        if signature is loader.get_unknown_sigature():
            return None
        return signature.determine_command_type(command_invocation, [], env_annotations)
