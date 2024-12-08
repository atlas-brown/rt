import logging
import os
import re
from typing import Dict, List, Optional, Tuple
from stream.command_signature import CommandSignature
from stream.signature_loader import SignatureLoader
from stream.shell_parser_util import extract_pipe_nodes_from_file, get_command_invocation, parse_shell_to_asts
from shasta.ast_node import *
from pash_annotations.parser.parser import parse as annot_parse
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
import tempfile

from stream.user_annotation import AnnotationType, UserAnnotation


ANNOTATION_PATTERN = re.compile(r'^\s*#\s*@(assume|assert|expect)\s+"(.+)"\s*-->\s*"(.+)"\s*$')

class ShellParser:
    def __init__(self, pipeline_address: str, enable_user_annotations: bool = True) -> None:
        self.signature_loader = SignatureLoader()
        self.pipeline_address = pipeline_address
        self.pipeline_nodes = extract_pipe_nodes_from_file(self.pipeline_address)

        if enable_user_annotations:
            self.annotations = self.extract_annotations_from_file()
        else:
            self.annotations = {}

    def parse_command_node(self, node: CommandInvocationInitial) -> Tuple[CommandSignature, CommandInvocationInitial]:
        assert isinstance(node, CommandInvocationInitial)
        for signature in self.signature_loader.signatures:
            if signature.matches_command(node):
                return (signature, node)
        logging.warning(f'No matching signature found for command {node.cmd_name if node.cmd_name != "xargs" else "xargs_" + node.operand_list[0].name}')
        return (self.signature_loader.get_unknown_sigature(), node)
        

    def parse_pipeline(self) -> List[List[Tuple[CommandSignature, CommandInvocationInitial]]]:
        if self.pipeline_nodes is None:
            raise ValueError("Parsing failed")
        
        pipelines: List[List[Tuple[CommandSignature, CommandInvocationInitial]]] = []
        for node in self.pipeline_nodes:
            commands_in_pipe : list[CommandInvocationInitial] = []
            for command_node in node.items:
                # cmd_raw = command_node.pretty()
                # parsed_command_invocation = annot_parse(cmd_raw)
                parsed_command_invocation = get_command_invocation(command_node)
                commands_in_pipe.append(parsed_command_invocation)
            pipelines.append([self.parse_command_node(command) for command in commands_in_pipe])
        return pipelines
    
    # to handle the difference between the original command and the parsed command (pretty version)
    # current solution is using a temp file to parse the command and get the pretty version
    def refine_command(self, command: str) -> str:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=True) as temp_file:
            temp_file.write(command)
            temp_file.flush()
            
            ast_nodes = parse_shell_to_asts(temp_file.name)
            
            if ast_nodes is None or len(ast_nodes) == 0:
                raise ValueError(f"Parsing failed: {command}")
                
            return ast_nodes[0][0].pretty()

    def extract_annotations_from_file(self) -> Dict[CommandNode, list[UserAnnotation]]:
        annotations: Dict[CommandNode, list[UserAnnotation]] = {}
        script_content = []
        with open(self.pipeline_address) as f:
            for line in f:
                script_content.append(line)
        for node in self.pipeline_nodes:
            try:
                line_number = node.items[0].line_number
                while True:
                    # the possible annotation line should be at least 1 line above the command line, and the 1st line is at script_content[0]
                    if line_number < 2:
                        break
                    line = script_content[line_number - 2]
                    res = ANNOTATION_PATTERN.match(line)
                    if res is None:
                        break
                    annotation_type = AnnotationType(res.group(1))
                    match annotation_type:
                        case AnnotationType.ASSUME | AnnotationType.ASSERT:
                            command = res.group(2)
                            pattern = res.group(3)
                        case AnnotationType.EXPECT:
                            pattern = res.group(2)
                            command = res.group(3)
                        case _:
                            raise ValueError("Invalid annotation type")
                    
                    command = self.refine_command(command)
                    
                    for command_node in node.items:
                        if command_node.pretty() == command:
                            corresponding_annotations = annotations.get(command_node, [])
                            corresponding_annotations.append(UserAnnotation(annotation_type, pattern, node, command_node))
                            annotations[command_node] = corresponding_annotations
                            break
                    line_number -= 1
                    
                    
            except Exception as e:
                logging.error(f"Error while extracting annotations: {e}")
        return annotations

                    
