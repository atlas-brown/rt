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

        env: Dict[str, str] = {}
        for i, arg in enumerate(self.args):
            arg_name = arg['name']
            if i < len(parsed_command_node.operand_list):
                env[arg_name] = parsed_command_node.operand_list[i].name

        # add predefined variables to env
        env["actual_input_type"] = previous_output_type.pattern
        env["output_type"] = self.default_output_type.pattern
        env["input_type"] = self.default_input_type.pattern

        parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_node.flag_option_list))
        parsed_args = set(env.keys())

        for rule in self.rules: # iterate over all rules, from top to bottom
            required_flags = set(rule['condition'].get('flags', []))
            required_args = set(rule['condition'].get('args', []))
            no_flags = set(rule['condition'].get('no_flags', []))
            no_args = set(rule['condition'].get('no_args', []))

            # match the rule, required flags and args are subset of actual flags and args, and no_flags and no_args are not in actual flags and args
            if (required_flags.issubset(parsed_flags) and
                required_args.issubset(parsed_args) and
                not any(flag in parsed_flags for flag in no_flags) and
                not any(arg in parsed_args for arg in no_args)):

                # update env
                update_variables: Dict[str, str] = rule.get('update', {}).copy()
                logging.debug(f"Command: {self.command_name}, Rule: {rule['condition']} -> {rule['update']}")
                for key, value in update_variables.items():
                    # find all {{variable}} in rule_env[key], replace them with env[variable]
                    # { or } are not allowed in variable names
                    update_variables[key] = re.sub(r"{{([^{}]*)}}", lambda match: env[match.group(1)], value)
                env.update(update_variables)
                logging.debug(f"Command: {self.command_name}, Updated env: {env}")

        logging.debug(f"Command: {self.command_name}, Expected Input type: {env['input_type']}, Output type (if compatible): {env['output_type']}")
        logging.debug("------------------------------")
        
        return RegularType(env['input_type']), RegularType(env['output_type'])
    
    def __repr__(self) -> str:
        return f"CommandSignature({self.command_name}, {self.default_input_type}, {self.default_output_type}, {self.args}, {self.flags}, {self.rules})"
