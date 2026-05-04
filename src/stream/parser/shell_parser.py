import logging
import os
import re
import tempfile
from typing import Dict, List, Optional, Tuple
from stream.command_signature import CommandSignature
from stream.signature_loader import SignatureLoader
from stream.parser.shell_parser_util import extract_pipe_nodes_from_file, get_command_invocation, parse_shell_to_asts
from shasta.ast_node import *
from pash_annotations.parser.parser import parse as annot_parse
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from stream.tool_error import PashAnnotationParsingError
from stream.utils.function_timer import timer

from stream.user_annotation import AnnotationType, EnvAnnotation, UserAnnotation


ANNOTATION_PATTERN = re.compile(
    r'^\s*#\s*@(assume|assert|expect|assert_contains)\s*"(.*)"\s*-->\s*"(.*)"\s*$'
    r'|^\s*#\s*@(concretize)\s*"(.*)"\s*-->\s*"(.*)"\s*$'
    r'|^\s*#\s*@(input|output|output_contains)\s*"(.*)"\s*$'
    r'|^\s*#\s*@(file|var)\s*"(.*)"\s*:\s*"(.*)"\s*$'
)

class ShellParser:
    @timer
    def __init__(
        self,
        pipeline_address: str,
        enable_user_annotations: bool = True,
        extract_all_pipelines: bool = True,
        enable_concretization: bool = True,
    ) -> None:
        self.signature_loader = SignatureLoader.get_instance()
        self.pipeline_address = pipeline_address
        self.enable_user_annotations = enable_user_annotations
        self.enable_concretization = enable_concretization
        
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
            self.pipeline_nodes: list[PipeNode] = []
            self.enable_line_map = {}
            for node, enable_line in pipeline_result:
                self.pipeline_nodes.append(node)
                self.enable_line_map[node] = enable_line
        else:
            # In normal mode, we just get pipeline nodes
            self.pipeline_nodes = pipeline_result
            self.enable_line_map = {}

        if enable_user_annotations or enable_concretization:
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
        return (self.signature_loader.get_unknown_sigature(), node)
        
    @timer
    def parse_pipeline(self) -> List[List[Tuple[CommandSignature, CommandInvocationInitial]]]:
        if self.pipeline_nodes is None:
            raise ValueError("Parsing failed")
        
        pipelines: List[List[Tuple[CommandSignature, CommandInvocationInitial]]] = []
        for node in self.pipeline_nodes:
            commands_in_pipe : list[CommandInvocationInitial] = []
            for command_node in node.items:
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

    @staticmethod
    def _normalize_annotation_var(var: str) -> str:
        # Keep the same shell-variable normalization used by @file/@var.
        return re.sub(r'\$(?!\{)([A-Za-z_][A-Za-z0-9_]*|[0-9]+)', r'${\1}', var)

    @staticmethod
    def _escape_concrete_line(line: str) -> str:
        escaped = []
        special_chars = set(r'\|&~*+?.^$()[]{}')
        for char in line:
            if char == "\t":
                escaped.append(r"\t")
            elif char == "\r":
                escaped.append(r"\r")
            elif char in special_chars:
                escaped.append("\\" + char)
            else:
                escaped.append(char)
        return "".join(escaped)

    def _concretize_file_to_pattern(self, path: str) -> str:
        file_path = path
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.path.dirname(self.pipeline_address), file_path)

        with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()

        seen = set()
        escaped_lines = []
        for line in lines:
            if line in seen:
                continue
            seen.add(line)
            escaped_lines.append(self._escape_concrete_line(line))

        if not escaped_lines:
            return ""
        if len(escaped_lines) == 1:
            return escaped_lines[0]
        return "(" + "|".join(escaped_lines) + ")"

    def _add_concretize_annotation(
        self,
        node: PipeNode,
        var: str,
        pattern: str,
        annotation_line: str,
        env_annotations: Dict[PipeNode, Dict[str, List[EnvAnnotation]]],
    ) -> None:
        var = self._normalize_annotation_var(var)
        corresponding_annotations = env_annotations.get(node).get(var, [])
        corresponding_annotations.append(
            EnvAnnotation(AnnotationType.CONCRETIZE, var, pattern, node, annotation_line)
        )
        env_annotations.get(node)[var] = corresponding_annotations

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
                    elif res.group(7) is not None:
                        annotation_type = AnnotationType(res.group(7))
                    else:
                        annotation_type = AnnotationType(res.group(9))
                    
                    match annotation_type:
                        case AnnotationType.INPUT | AnnotationType.OUTPUT | AnnotationType.OUTPUT_CONTAINS:
                            pattern = res.group(8)
                            command = None
                        case AnnotationType.ASSUME | AnnotationType.ASSERT | AnnotationType.ASSERT_CONTAINS:
                            command = res.group(2)
                            pattern = res.group(3)
                        case AnnotationType.EXPECT:
                            pattern = res.group(2)
                            command = res.group(3)
                        case AnnotationType.CONCRETIZE:
                            var = res.group(5)
                            pattern = res.group(6)
                        case AnnotationType.VAR | AnnotationType.FILE:
                            var = res.group(10)
                            pattern = res.group(11)
                        case _:
                            raise ValueError("Invalid annotation type")

                    if annotation_type == AnnotationType.CONCRETIZE:
                        if self.enable_concretization:
                            concrete_pattern = self._concretize_file_to_pattern(pattern)
                            self._add_concretize_annotation(
                                node,
                                var,
                                concrete_pattern,
                                line,
                                env_annotations,
                            )
                        continue

                    if not self.enable_user_annotations:
                        continue
                    
                    # Process each annotation type
                    if annotation_type == AnnotationType.INPUT:
                        input_pattern = pattern
                        # Store input pattern in env_annotations under a special key
                        env_annotations[node]["__input_pattern__"] = [EnvAnnotation(AnnotationType.INPUT, "__input_pattern__", pattern, node, line)]
                        continue
                    
                    if annotation_type == AnnotationType.OUTPUT or annotation_type == AnnotationType.OUTPUT_CONTAINS:
                        corresponding_annotations = annotations.get(node.items[-1], [])
                        updated_type = AnnotationType.ASSERT if annotation_type == AnnotationType.OUTPUT else AnnotationType.ASSERT_CONTAINS
                        corresponding_annotations.append(UserAnnotation(updated_type, pattern, node, node.items[-1], line))
                        annotations[node.items[-1]] = corresponding_annotations
                        continue
                    
                    if annotation_type == AnnotationType.VAR or annotation_type == AnnotationType.FILE:
                        # $1 -> ${1}
                        var = self._normalize_annotation_var(var)
                        corresponding_annotations = env_annotations.get(node).get(var, [])
                        corresponding_annotations.append(EnvAnnotation(annotation_type, var, pattern, node, line))
                        env_annotations.get(node)[var] = corresponding_annotations
                        continue

                    if command:
                        # Annotation fields are double-quoted, so command snippets may
                        # escape embedded shell quotes.  The shell parser should see the
                        # command the script sees, not the annotation delimiter escapes.
                        refined_command = self.refine_command(command.replace(r'\"', '"'))
                        
                        for command_node in node.items:
                            if command_node.pretty() == refined_command:
                                corresponding_annotations = annotations.get(command_node, [])
                                corresponding_annotations.append(UserAnnotation(annotation_type, pattern, node, command_node, line))
                                annotations[command_node] = corresponding_annotations
                                break
            except Exception as e:
                logging.error(f"Error while extracting annotations: {e}")
        
        return annotations, input_pattern, env_annotations

                    
