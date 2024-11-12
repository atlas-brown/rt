import logging
from typing import Any, Dict, List, Tuple
from stream.command_signature import CommandSignature
from stream.signature_loader import SignatureLoader
from stream.shell_parser import parse_shell_to_asts
from stream.symb import nodes_from_file
from shasta.ast_node import *
from pash_annotations.parser.parser import parse as annot_parse
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial


class PipelineParser:
    def __init__(self, pipeline_address: str) -> None:
        self.signature_loader = SignatureLoader()
        self.pipeline_address = pipeline_address
        self.pipeline_nodes : list[AstNode] = self.parse_shell_script()

    def parse_shell_script(self) -> List[AstNode]:
        return nodes_from_file(self.pipeline_address)

    def parse_command_node(self, node: CommandInvocationInitial) -> Tuple[CommandSignature, CommandInvocationInitial]:
        assert isinstance(node, CommandInvocationInitial)
        for signature in self.signature_loader.signatures:
            if signature.matches_command(node):
                return (signature, node)
        # raise ValueError(f'No matching signature found for command {node.cmd_name if node.cmd_name != "xargs" else "xargs_" + node.operand_list[0].name}')
        logging.warning(f'No matching signature found for command {node.cmd_name if node.cmd_name != "xargs" else "xargs_" + node.operand_list[0].name}')
        return (self.signature_loader.get_unknown_sigature(), node)
        

    def parse_pipeline(self) -> List[List[Tuple[CommandSignature, CommandInvocationInitial]]]:
        if self.pipeline_nodes is None:
            raise ValueError("Parsing failed")
        
        pipelines: List[List[Tuple[CommandSignature, CommandInvocationInitial]]] = []
        for node in self.pipeline_nodes:
            commands_in_pipe : list[CommandInvocationInitial] = []
            for command_node in node.items:
                # assert (isinstance(command_node, CommandNode))
                cmd_raw = command_node.pretty()
                commands_in_pipe.append(annot_parse(cmd_raw))
            pipelines.append([self.parse_command_node(command) for command in commands_in_pipe])
        return pipelines
