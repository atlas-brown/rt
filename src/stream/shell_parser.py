import logging
import os
import re
import tempfile
from typing import Dict, List, Optional, Tuple
from stream.command_signature import CommandSignature
from stream.signature_loader import SignatureLoader
from stream.shell_parser_util import extract_pipe_nodes_from_file, get_command_invocation, parse_shell_to_asts
from shasta.ast_node import *
from pash_annotations.parser.parser import parse as annot_parse
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from stream.tool_error import PashAnnotationParsingError
from stream.function_timer import timer

from stream.user_annotation import AnnotationType, EnvAnnotation, UserAnnotation


ANNOTATION_PATTERN = re.compile(r'^\s*#\s*@(assume|assert|expect|assert_contains)\s*"(.*)"\s*-->\s*"(.*)"\s*$|^\s*#\s*@(input|output|output_contains)\s*"(.*)"\s*$|^\s*#\s*@(file|var)\s*"(.*)"\s*:\s*"(.*)"\s*$')

class ShellParser:
    @timer
    def __init__(self, pipeline_address: str, enable_user_annotations: bool = True, extract_all_pipelines: bool = True) -> None:
        self.signature_loader = SignatureLoader.get_instance()
        self.pipeline_address = pipeline_address
        
        # Check for stream disable in first two lines if extract_all_pipelines is True
        if extract_all_pipelines:
            with open(pipeline_address, 'r') as f:
                first_two_lines = [f.readline().strip(), f.readline().strip()]
                if any("# stream disable" in line for line in first_two_lines):
                    extract_all_pipelines = False
        
        self.extract_all_pipelines = extract_all_pipelines
        
        # Get pipeline nodes, possibly with their corresponding enable line numbers
        pipeline_result = extract_pipe_nodes_from_file(self.pipeline_address, self.extract_all_pipelines)
        
        # Handle result based on extraction mode
        if not self.extract_all_pipelines:
            # In stream enable mode, we get tuples of (pipeline_node, enable_line)
            self.pipeline_nodes = []
            self.enable_line_map = {}
            for node, enable_line in pipeline_result:
                self.pipeline_nodes.append(node)
                self.enable_line_map[node] = enable_line
        else:
            # In normal mode, we just get pipeline nodes
            self.pipeline_nodes = pipeline_result
            self.enable_line_map = {}

        if enable_user_annotations:
            self.annotations, self.input_pattern, self.env_annotations = self.extract_annotations_from_file()
            logging.debug(f"Annotations: {self.annotations}")
            logging.debug(f"Env Annotations: {self.env_annotations}")
        else:
            self.annotations = {}
            self.input_pattern = None
            self.env_annotations = {}

    @timer
    def parse_command_node(self, node: CommandInvocationInitial) -> Tuple[CommandSignature, CommandInvocationInitial]:
        assert isinstance(node, CommandInvocationInitial)
        for signature in self.signature_loader.signatures:
            if signature.matches_command(node):
                return (signature, node)
        logging.warning(f'No matching signature found for command {node.cmd_name if node.cmd_name != "xargs" or len(node.operand_list) == 0 else "xargs_" + node.operand_list[0].name}')
        return (self.signature_loader.get_unknown_sigature(), node)
        
    @timer
    def parse_pipeline(self) -> List[List[Tuple[CommandSignature, CommandInvocationInitial]]]:
        if self.pipeline_nodes is None:
            raise ValueError("Parsing failed")
        
        pipelines: List[List[Tuple[CommandSignature, CommandInvocationInitial]]] = []
        for node in self.pipeline_nodes:
            commands_in_pipe : list[CommandInvocationInitial] = []
            for command_node in node.items:
                # try:
                #     cmd_raw = command_node.pretty()
                #     parsed_command_invocation = annot_parse(cmd_raw)
                # except Exception as e:
                #     raise PashAnnotationParsingError(f"Failed to parse command: {cmd_raw}, error: {e}")
                #     # logging.warning(f"Failed to parse command: {cmd_raw}, error: {e}")
                #     # parsed_command_invocation = CommandInvocationInitial("parsed_fail_command", [], [])
                parsed_command_invocation = get_command_invocation(command_node)
                commands_in_pipe.append(parsed_command_invocation)
            pipelines.append([self.parse_command_node(command) for command in commands_in_pipe])
        return pipelines
    
    # to handle the difference between the original command and the parsed command (pretty version)
    # current solution is using a temp file to parse the command and get the pretty version
    @timer
    def refine_command(self, command: str) -> str:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=True) as temp_file:
            temp_file.write(command)
            temp_file.flush()
            
            ast_nodes = parse_shell_to_asts(temp_file.name)
            
            if ast_nodes is None or len(ast_nodes) == 0:
                raise ValueError(f"Parsing failed: {command}")
                
            return ast_nodes[0][0].pretty()

    @timer
    def extract_annotations_from_file(self) -> Tuple[Dict[CommandNode, list[UserAnnotation]], Optional[str], Dict[PipeNode, Dict[str, List[EnvAnnotation]]]]:
        annotations: Dict[CommandNode, list[UserAnnotation]] = {}
        input_pattern = None
        script_content = []
        env_annotations: Dict[PipeNode, Dict[str, List[EnvAnnotation]]] = {}
        
        with open(self.pipeline_address) as f:
            script_content = f.readlines()

        for node in self.pipeline_nodes:
            env_annotations[node] = {}
            try:
                # Determine the line number to use for annotations
                if not self.extract_all_pipelines and node in self.enable_line_map:
                    # For a stream enable pipeline, use the stream enable line number
                    line_number = self.enable_line_map[node] + 1  # +1 because we'll look at the line above
                else:
                    # For normal pipelines, use the node's line number
                    line_number = node.items[0].line_number
                
                # Look for annotations above the relevant line
                while True:
                    # Stop if we've reached the top of the file
                    if line_number < 2:
                        break
                    
                    # Check the line above for annotations
                    line = script_content[line_number - 2]
                    line_number -= 1
                    
                    # Parse the annotation if present
                    res = ANNOTATION_PATTERN.match(line)
                    if res is None:
                        break
                    
                    # Extract annotation type and data
                    if res.group(1) is not None:
                        annotation_type = AnnotationType(res.group(1))
                    elif res.group(4) is not None:
                        annotation_type = AnnotationType(res.group(4))
                    else:
                        annotation_type = AnnotationType(res.group(6))
                    
                    match annotation_type:
                        case AnnotationType.INPUT | AnnotationType.OUTPUT | AnnotationType.OUTPUT_CONTAINS:
                            pattern = res.group(5)
                            command = None
                        case AnnotationType.ASSUME | AnnotationType.ASSERT | AnnotationType.ASSERT_CONTAINS:
                            command = res.group(2)
                            pattern = res.group(3)
                        case AnnotationType.EXPECT:
                            pattern = res.group(2)
                            command = res.group(3)
                        case AnnotationType.VAR | AnnotationType.FILE:
                            var = res.group(7)
                            pattern = res.group(8)
                        case _:
                            raise ValueError("Invalid annotation type")
                    
                    # Process each annotation type
                    if annotation_type == AnnotationType.INPUT:
                        input_pattern = pattern
                        # Store input pattern in env_annotations under a special key
                        env_annotations[node]["__input_pattern__"] = [EnvAnnotation(AnnotationType.INPUT, "__input_pattern__", pattern, node)]
                        continue
                    
                    if annotation_type == AnnotationType.OUTPUT or annotation_type == AnnotationType.OUTPUT_CONTAINS:
                        corresponding_annotations = annotations.get(node.items[-1], [])
                        updated_type = AnnotationType.ASSERT if annotation_type == AnnotationType.OUTPUT else AnnotationType.ASSERT_CONTAINS
                        corresponding_annotations.append(UserAnnotation(updated_type, pattern, node, node.items[-1]))
                        annotations[node.items[-1]] = corresponding_annotations
                        continue
                    
                    if annotation_type == AnnotationType.VAR or annotation_type == AnnotationType.FILE:
                        # $1 -> ${1}
                        var = re.sub(r'\$(.+)(?!\})', r'${\1}', var)
                        corresponding_annotations = env_annotations.get(node).get(var, [])
                        corresponding_annotations.append(EnvAnnotation(annotation_type, var, pattern, node))
                        env_annotations.get(node)[var] = corresponding_annotations
                        continue

                    if command:
                        refined_command = self.refine_command(command)
                        
                        for command_node in node.items:
                            if command_node.pretty() == refined_command:
                                corresponding_annotations = annotations.get(command_node, [])
                                corresponding_annotations.append(UserAnnotation(annotation_type, pattern, node, command_node))
                                annotations[command_node] = corresponding_annotations
                                break
            except Exception as e:
                logging.error(f"Error while extracting annotations: {e}")
        
        return annotations, input_pattern, env_annotations

                    
