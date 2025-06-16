import logging
from stream.utils.logger import get_logger
from stream.regular_type import RegularType
import re
from typing import List, Dict, Any, Optional, Tuple
from shasta.ast_node import *
from pash_annotations.parser.parser import parse as annot_parse
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from stream.tool_error import ToolError, PashAnnotationParsingError
from stream.user_annotation import AnnotationType, EnvAnnotation, UserAnnotation

class CommandSignature:
    def __init__(
        self, 
        command_name: str, 
        default_input_type: str, 
        default_output_type: str, 
        args: List[Dict[str, Any]], 
        flags: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
        isInteresting: bool,
        isTainted: bool
    ) -> None:
        self.command_name = command_name
        self.default_input_type = RegularType(default_input_type)
        self.default_output_type = RegularType(default_output_type)
        self.args = args
        self.flags = flags
        self.rules = rules
        self.isInteresting = isInteresting
        self.isTainted = isTainted
    def matches_command(self, command_invocation: CommandInvocationInitial) -> bool:
        assert isinstance(command_invocation, CommandInvocationInitial)
        if command_invocation.cmd_name == self.command_name:
            return True
        if command_invocation.cmd_name == "xargs":
            if len(command_invocation.operand_list) == 0:
                return False
            if "xargs_" + command_invocation.operand_list[0].name == self.command_name:
                return True
        return False
    
    # FIXME: simplify the return type
    # dont override this method, override output_type_inference instead
    def determine_output_type(self, previous_output_type: RegularType, parsed_command_invocation: CommandInvocationInitial, user_annotations: List[UserAnnotation], env_annotations: Dict[str, List[EnvAnnotation]]) -> RegularType:
        # if user annotation (assume) is available, use it
        # otherwise, use inference
        for annotation in user_annotations:
            if annotation.annotation_type == AnnotationType.ASSUME:
                get_logger().get_latest_record()["command_list"][-1]["output_type"] = annotation.pattern
                get_logger().get_latest_record()["command_list"][-1]["output_assumed"] = annotation.pattern
                return RegularType(annotation.pattern, tainted=False)
            
        if parsed_command_invocation.cmd_name != "xargs" and len(parsed_command_invocation.operand_list) >= 1 and self.isInteresting:
            operand = parsed_command_invocation.operand_list[0].name
            if operand.startswith("-"):
                raise PashAnnotationParsingError(f"pash_annotations.parser might be wrong, command: {parsed_command_invocation}, operand: {operand}")
        
        flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
        if "--version" in flags or "--help" in flags:
            get_logger().get_latest_record()["command_list"][-1]["output_type"] = ".*"
            return RegularType(".*")
        previous_output_type, trans_to_line_based = self.process_stream_input(previous_output_type)
        out = self.output_type_inference(previous_output_type, parsed_command_invocation, env_annotations)
        if trans_to_line_based:
            original_output_type = get_logger().get_latest_record()["command_list"][-1]["output_type"]
            get_logger().get_latest_record()["command_list"][-1]["output_type"] = original_output_type.replace("α", "line-extract(α, .*)")
            get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = True
        return out
    
    def process_stream_input(self, previous_output_type: RegularType) -> Tuple[RegularType, bool]:
        if previous_output_type.repr_mode == "stream":
            return previous_output_type.to_line_based_repr(), True
        return previous_output_type, False


    def get_operands(self, parsed_command_node: CommandInvocationInitial) -> List[str]:
        assert isinstance(parsed_command_node, CommandInvocationInitial)
        operand_list = parsed_command_node.operand_list.copy()
        if len(operand_list) == 0:
            return []
        if parsed_command_node.cmd_name == "xargs":
            return [operand.name for operand in operand_list[1:]]
        return [operand.name for operand in operand_list]
    

    def get_file_name(self, parsed_command_invocation: CommandInvocationInitial, env_annotations: Dict[str, List[EnvAnnotation]]) -> RegularType:
        file_name = parsed_command_invocation.operand_list[-1].name
        for annotation in env_annotations.get(file_name, []):
            if annotation.annotation_type == AnnotationType.FILE:
                return RegularType(annotation.pattern, tainted=False)
        return RegularType(".*")

    def output_type_inference(self, previous_output_type: RegularType, parsed_command_invocation: CommandInvocationInitial, env_annotations: Dict[str, List[EnvAnnotation]]) -> RegularType:
        assert isinstance(previous_output_type, RegularType)
        assert isinstance(parsed_command_invocation, CommandInvocationInitial)
        lose_precision = True
        tainted = self.isTainted

        env: Dict[str, RegularType] = {}
        env_raw: Dict[str, str] = {}

        for i, arg in enumerate(self.args):
            arg_name: str = arg['name']
            is_regex: bool = arg.get('is_regex', False)
            if i < len(parsed_command_invocation.operand_list):
                arg = parsed_command_invocation.operand_list[i].name
                env_raw[arg_name] = arg
                
                # Check for FILE annotation with exact pattern match
                if arg in env_annotations:
                    for annot in env_annotations[arg]:
                        if annot.annotation_type == AnnotationType.FILE:
                            env[f"{arg_name}.content"] = RegularType(annot.pattern)
                            lose_precision = False
                            tainted = False
                            break
                if f"{arg_name}.content" not in env:
                    env[f"{arg_name}.content"] = RegularType(".*")
                    lose_precision = True
                    tainted = True
                
                # Process ${} patterns and escape non-pattern parts if not regex
                parts = []
                last_end = 0
                for var_match in re.finditer(r'(\$\{.*?\})', arg):
                    # Add text before match (escaped if not regex)
                    if var_match.start() > last_end:
                        text = arg[last_end:var_match.start()]
                        parts.append(re.escape(text) if not is_regex else text)
                    
                    # Add the variable pattern
                    var_name = var_match.group(1)
                    var_pattern = ".*"  # Default pattern if not found
                    
                    if var_name in env_annotations:
                        for annot in env_annotations[var_name]:
                            if annot.annotation_type == AnnotationType.VAR:
                                var_pattern = annot.pattern
                                tainted = False
                                lose_precision = False
                                break
                    
                    parts.append(var_pattern)
                    last_end = var_match.end()
                
                # Add remaining text (escaped if not regex)
                if last_end < len(arg):
                    text = arg[last_end:]
                    parts.append(re.escape(text) if not is_regex else text)
                
                if parts:
                    # Joined parts with variable substitutions
                    env[arg_name] = RegularType(''.join(parts))
                else:
                    # No matches found, escape if not regex
                    env[arg_name] = RegularType(re.escape(arg) if not is_regex else arg)

        # add predefined variables to env
        env["actual_input_type"] = previous_output_type
        env["output_type"] = self.default_output_type
        command_list = get_logger().get_latest_record()["command_list"]
        command_list[-1]["output_type"] = self.default_output_type.pattern

        parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
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
                update_variables: Dict[str, RegularType | str] = rule.get('update', {}).copy()
                logging.debug(f"Command: {self.command_name}, Rule: {rule['condition']} -> {rule['update']}")
                if "output_type" in update_variables:
                    output_type_str = update_variables["output_type"].replace("{{actual_input_type}}", "α")
                    for key, value in env.items():
                        if isinstance(value, RegularType) and value.pattern is not None:
                            output_type_str = output_type_str.replace(f"{{{{{key}}}}}", value.pattern)
                        elif isinstance(value, str):
                            output_type_str = output_type_str.replace(f"{{{{{key}}}}}", value)
                    get_logger().get_latest_record()["command_list"][-1]["output_type"] = output_type_str
                for key, value in update_variables.items():
                    try:
                        update_variables[key] = RegularType(value, hole_dict=env)
                    except:
                        raise ToolError(f"Error in updating env for command, missing argument when updating {key} with {value}")
                env.update(update_variables)
                logging.debug(f"Command: {self.command_name}, Updated env: {env}")
                if rule.get('output_tainted', tainted):
                    tainted = rule.get('output_tainted', tainted)
                    lose_precision = tainted
                if rule.get('stop', False):
                    break

        logging.debug(f"Command: {self.command_name}, Output type (if compatible): {env['output_type']}")
        logging.debug("-"*60)
        env['output_type'].tainted = tainted
        get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = lose_precision
        return env['output_type']
    
    # dont override this method, override get_input_type instead
    def determine_input_type(self, parsed_command_invocation: CommandInvocationInitial, user_annotations: List[UserAnnotation], heuristic_rules: List[str], env_annotations: Dict[str, List[EnvAnnotation]]) -> Tuple[RegularType, Optional[RegularType]]:
        assert isinstance(parsed_command_invocation, CommandInvocationInitial)

        # if user annotation (expect) is available, use it
        for annotation in user_annotations:
            if annotation.annotation_type == AnnotationType.EXPECT:
                return RegularType(annotation.pattern), None
            
        return self.get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)
    
    def get_input_type(self, parsed_command_invocation: CommandInvocationInitial, heuristic_rules: List[str], env_annotations: Dict[str, List[EnvAnnotation]]) -> Tuple[RegularType, Optional[RegularType]]:

        input_type = self.default_input_type.pattern

        no_input_type = None

        parsed_args = set(map(lambda arg: arg['name'], self.args[:len(self.get_operands(parsed_command_invocation))]))

        parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))

        heuristic_rules = set(heuristic_rules)

        for rule in self.rules: # iterate over all rules, from top to bottom
            required_flags = set(rule['condition'].get('flags', []))
            required_args = set(rule['condition'].get('args', []))
            no_flags = set(rule['condition'].get('no_flags', []))
            no_args = set(rule['condition'].get('no_args', []))
            required_heuristics = set(rule['condition'].get('heuristics', []))

            # match the rule, required flags and args are subset of actual flags and args, and no_flags and no_args are not in actual flags and args
            if (required_flags.issubset(parsed_flags) and
                required_args.issubset(parsed_args) and
                not any(flag in parsed_flags for flag in no_flags) and
                not any(arg in parsed_args for arg in no_args) and
                required_heuristics.issubset(heuristic_rules)):

                # update input type
                update_variables: Dict[str, str] = rule.get('update', {}).copy()
                for key, value in update_variables.items():
                    if key == 'input_type':
                        input_type = value
                    if key == "no_input_type":
                        no_input_type = value
                logging.debug(f"Command: {self.command_name}, Updated input type: {input_type}")
                if rule.get('stop', False):
                    break

        logging.debug(f"Command: {self.command_name}, Expected input type: {input_type}")
        
        return RegularType(input_type), RegularType(no_input_type) if no_input_type is not None else None
    
    def __repr__(self) -> str:
        return f"CommandSignature({self.command_name}, {self.default_input_type}, {self.default_output_type}, {self.args}, {self.flags}, {self.rules})"
