import logging
from stream.regular_type import RegularType
import re
from typing import List, Dict, Any, Optional, Tuple
from shasta.ast_node import *
from pash_annotations.parser.parser import parse as annot_parse
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

class CommandSignature:
    def __init__(
        self, 
        command_name: str, 
        format: List[str], 
        default_input_type: str, 
        default_output_type: str, 
        args: List[Dict[str, Any]], 
        flags: List[Dict[str, Any]],
        rules: List[Dict[str, Any]]
    ) -> None:
        self.command_name = command_name
        self.format = format
        self.default_input_type = RegularType(default_input_type)
        self.default_output_type = RegularType(default_output_type)
        self.args = args
        self.flags = flags
        self.rules = rules
        self.regex = self.format_to_regex()

    def format_to_regex(self) -> re.Pattern:
        regex_parts = map(lambda element: r".*" if element.startswith("arg") or element.startswith("flag") else re.escape(element), self.format)
        regex_pattern = "".join(regex_parts)
        return re.compile(f"^{regex_pattern}$")

    def matches_command(self, node: CommandInvocationInitial) -> bool:
        # assert len(self.format) > 0
        assert isinstance(node, CommandInvocationInitial)
        # need to be more precise
        return self.command_name == node.cmd_name

    # def extract_flags_and_args(self, node: CommandInvocationInitial) -> Tuple[List[str], Dict[str, List[str]]]:
        parsed_flags: List[str] = [] # [flag_name] e.g., ["-v", "-i"]
        parsed_args: Dict[List[str]] = {} # {arg_name: [arg_value]}, e.g., {"pattern: ["123"]"}

        index = 0
        arg_index = 0
        for element in self.format:
            match element:
                case "flag?":
                    if index < len(command_parts) and self.is_flag(command_parts[index]):
                        parsed_flags.append(command_parts[index])
                        flag_name = command_parts[index]
                        flag = next((flag for flag in self.flags if flag['name'] == flag_name), None)
                        if flag is not None and flag.get('argument', True):
                            index += 2
                        else:
                            index += 1
                case "arg":
                    if index < len(command_parts):
                        parsed_args[self.args[arg_index]['name']] = [command_parts[index]]
                        index += 1
                        arg_index += 1
                    else:
                        raise ValueError(f"Missing required argument for {self.command_name}.")
                case "arg?":
                    if index < len(command_parts):
                        parsed_args[self.args[arg_index]['name']] = [command_parts[index]]
                        index += 1
                        arg_index += 1
                    else:
                        parsed_args[self.args[arg_index]['name']] = []
                case "arg+":
                    parsed_args[self.args[arg_index]['name']] = []
                    while index < len(command_parts):
                        parsed_args[self.args[arg_index]['name']].append(command_parts[index])
                        index += 1
                    arg_index += 1
                case _:
                    index += 1

        return parsed_flags, parsed_args

    # def is_flag(self, arg: str) -> bool:
    #     # need to be refined
    #     return arg.startswith("-") and len(arg) > 1

    def determine_input_output_type(self, previous_output_type: RegularType, parsed_command_node: CommandInvocationInitial) -> Tuple[RegularType, RegularType]:
        assert isinstance(previous_output_type, RegularType)
        assert isinstance(parsed_command_node, CommandInvocationInitial)

        structured_args: Dict[str, Optional[str]] = {}
        for i, arg in enumerate(self.args):
            arg_name = arg['name']
            if i < len(parsed_command_node.operand_list):
                structured_args[arg_name] = parsed_command_node.operand_list[i].name
            else:
                structured_args[arg_name] = None

        # for arg in self.args:
        #     assert isinstance(arg['name'], str)
        #     arg_name = arg['name']
        #     if arg_name in map(lambda operand: operand.name
        #                        , parsed_command_node.operand_list):
        #         structured_args[arg_name] = parsed_command_node.operand_list[0].name
        #     else:
        #         structured_args[arg_name] = None

        for rule in self.rules:
            required_flags = set(rule['condition'].get('flags', []))
            # flag_option_list is union type Union[Flag, Option], I only need the flag part, and it should be flag.get_name()
            if required_flags.issubset(set(map(lambda flag: flag.get_name(), parsed_command_node.flag_option_list))):
                output_type_pattern: str = rule.get('output_type', self.default_output_type.pattern)
                input_type_pattern: str = rule.get('input_type', self.default_input_type.pattern)
                for arg in self.args:
                    arg_name = arg['name']
                    if arg_name in structured_args and structured_args[arg_name] is not None:
                        output_type_pattern = output_type_pattern.replace(f'{{{arg_name}}}', structured_args[arg_name]) # replace the placeholder with the actual value, r.g., grep {pattern} to grep 123
                print(f"Input type: {input_type_pattern}, Output type: {output_type_pattern}")
                return RegularType(input_type_pattern), RegularType(output_type_pattern)

        # if no rules match, return the default output type
        return self.default_input_type, self.default_output_type
    
    def __repr__(self) -> str:
        return f"CommandSignature({self.command_name}, {self.format}, {self.default_input_type}, {self.default_output_type}, {self.args}, {self.flags}, {self.rules})"
