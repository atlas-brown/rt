import re

from pash_annotations.datatypes.BasicDatatypes import Flag, Operand, Option
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_transform import Compose, Constant, Subtraction
from rt.regular_types.stream_type import StreamType


class FindResolver(RuleResolver):

    def resolve(
        self, invocation, user_annotations=None, env=None, heuristic_rules=None
    ):
        output_transform = self._construct_output_transform(invocation, env)
        return CommandType(None, output_transform)

    def _construct_output_transform(self, invocation, env):
        operands = [operand.name for operand in invocation.operand_list]
        exec_command, exec_name = self._extract_exec_command(operands)
        if exec_command is None:
            return Constant(self._infer_find_output_type(operands))

        exec_command_type = self._lookup_command_type(exec_command, env)
        if exec_command_type is None:
            return Constant(StreamType.from_pattern(".+"))

        if exec_command_type.is_simple():
            output_transform = exec_command_type.transform
        else:
            output_transform = Compose(
                exec_command_type.transform,
                Constant(StreamType.from_pattern(".+")),
            )

        if exec_name == "ls":
            output_transform = Subtraction(
                output_transform,
                Constant(StreamType.from_pattern("total .+")),
            )
        return output_transform

    def _infer_find_output_type(self, operands):
        output_type = StreamType.from_pattern(".+")
        if operands:
            search_path = operands[0]
            if not search_path.startswith("-"):
                name_pattern = None
                for i in range(len(operands) - 1):
                    if operands[i] == "-name" and i + 1 < len(operands):
                        name_pattern = operands[i + 1]
                        break

                if name_pattern and ("*" in name_pattern or "?" in name_pattern):
                    regex_pattern = (
                        re.escape(name_pattern).replace("\\*", ".*").replace("\\?", ".")
                    )
                    escaped_path = re.escape(search_path)
                    if search_path.endswith("/"):
                        output_type = StreamType.from_pattern(
                            f"{escaped_path}.*{regex_pattern}"
                        )
                    else:
                        output_type = StreamType.from_pattern(
                            f"{escaped_path}(/.*)?/{regex_pattern}"
                        )
                else:
                    escaped_path = re.escape(search_path)
                    if search_path.endswith("/"):
                        output_type = StreamType.from_pattern(f"{escaped_path}.*")
                    else:
                        output_type = StreamType.from_pattern(f"{escaped_path}(/.+)?")
        return output_type

    def _extract_exec_command(self, operands):
        for i in range(len(operands) - 3):
            if operands[i : i + 4] != ["-e", "-x", "-e", "-c"]:
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
                if arg.startswith("-"):
                    if "=" in arg:
                        option_name, option_arg = arg.split("=", 1)
                        flag_option_list.append(Option(option_name, option_arg))
                    else:
                        flag_option_list.append(Flag(arg))
                else:
                    operand_list.append(Operand(arg))

            return (
                CommandInvocationInitial(cmd_name, flag_option_list, operand_list),
                cmd_name,
            )
        return None, None

    def _lookup_command_type(self, command_invocation, env):
        from rt.regular_types.database.registry import get_type as types_get

        try:
            return types_get(command_invocation, [], {}, [])
        except Exception:
            return None


resolve = FindResolver
