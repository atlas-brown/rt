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

    def matches_command(self, node: CommandNode) -> bool:
        assert len(format) > 0
        return format[0] == node

    def extract_flags_and_args(self, command_parts: List[str]) -> Tuple[List[str], Dict[str, List[str]]]:
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

    def is_flag(self, arg: str) -> bool:
        # need to be refined
        return arg.startswith("-") and len(arg) > 1

    def determine_output_type(self, parsed_flags: List[str], parsed_args: Dict[str, List[str]], input_type: 'RegularType') -> RegularType:
        structured_args: Dict[str, Optional[str]] = {}
        for arg in self.args:
            arg_name = arg['name']
            if arg_name in parsed_args:
                structured_args[arg_name] = parsed_args[arg_name][0]
            else:
                structured_args[arg_name] = None

        for rule in self.rules:
            required_flags = set(rule['condition'].get('flags', []))
            if required_flags.issubset(parsed_flags):
                output_type: str = rule['output_type']
                for arg in self.args:
                    arg_name = arg['name']
                    if arg_name in structured_args and structured_args[arg_name] is not None:
                        output_type = output_type.replace(f'{{{arg_name}}}', structured_args[arg_name]) # replace the placeholder with the actual value, r.g., grep {pattern} to grep 123
                        
                return RegularType(output_type)

        # if no rules match, return the default output type
        return self.default_output_type
    
    def __repr__(self) -> str:
        return f"CommandSignature({self.command_name}, {self.format}, {self.default_input_type}, {self.default_output_type}, {self.args}, {self.flags}, {self.rules})"
