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
        default_input_type: str, 
        default_output_type: str, 
        args: List[Dict[str, Any]], 
        flags: List[Dict[str, Any]],
        rules: List[Dict[str, Any]]
    ) -> None:
        self.command_name = command_name
        self.default_input_type = RegularType(default_input_type)
        self.default_output_type = RegularType(default_output_type)
        self.args = args
        self.flags = flags
        self.rules = rules

    def matches_command(self, node: CommandInvocationInitial) -> bool:
        assert isinstance(node, CommandInvocationInitial)
        # need to be more precise
        return self.command_name == node.cmd_name

    def determine_input_output_type(self, previous_output_type: RegularType, parsed_command_node: CommandInvocationInitial) -> Tuple[RegularType, RegularType]:
        assert isinstance(previous_output_type, RegularType)
        assert isinstance(parsed_command_node, CommandInvocationInitial)

        # obtain the arguments {arg_name: arg_value} from the parsed command node, need to be more precise
        structured_args: Dict[str, str] = {}
        for i, arg in enumerate(self.args):
            arg_name = arg['name']
            if i < len(parsed_command_node.operand_list):
                structured_args[arg_name] = parsed_command_node.operand_list[i].name

        # determine the output type based rules, parametric polymorphism supported, e.g., grep .*{pattern}.*&{actual_input_type} can be resolved
        for rule in self.rules:  # match the condition of the rule, from top to bottom
            required_flags = set(rule['condition'].get('flags', []))
            required_args = set(rule['condition'].get('args', []))
            if required_flags.issubset(set(map(lambda flag_option: flag_option.get_name(), parsed_command_node.flag_option_list))) and required_args.issubset(set(structured_args.keys())):
                output_type_pattern: str = rule.get('output_type', self.default_output_type.pattern)
                input_type_pattern: str = rule.get('input_type', self.default_input_type.pattern)
                output_type_pattern = output_type_pattern.replace('{actual_input_type}', previous_output_type.pattern) # replace the placeholder with the actual input type
                for arg in self.args:
                    arg_name = arg['name']
                    if arg_name in structured_args:
                        output_type_pattern = output_type_pattern.replace(f'{{{arg_name}}}', structured_args[arg_name]) # replace the placeholder with the actual value, e.g., grep {pattern} to grep 123
                logging.debug(f"Input type: {input_type_pattern}, Output type: {output_type_pattern}")
                return RegularType(input_type_pattern), RegularType(output_type_pattern)

        # if no rules match, return the default output type
        return self.default_input_type, self.default_output_type
    
    def __repr__(self) -> str:
        return f"CommandSignature({self.command_name}, {self.default_input_type}, {self.default_output_type}, {self.args}, {self.flags}, {self.rules})"
