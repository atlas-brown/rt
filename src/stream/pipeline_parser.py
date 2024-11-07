import logging
from typing import Any, Dict, List, Tuple
from stream.command_signature import CommandSignature
from stream.signature_loader import SignatureLoader
from stream.shell_parser import parse_shell_to_asts
from shasta.ast_node import *
from pash_annotations.parser.parser import parse as annot_parse
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial


class PipelineParser:
    def __init__(self, pipeline_address: str) -> None:
        self.signature_loader = SignatureLoader()
        self.pipeline_address = pipeline_address
        self.ast : list[AstNode] = self.parse_shell_script()

    def parse_shell_script(self) -> List[AstNode]:
        return parse_shell_to_asts(self.pipeline_address)

    def parse_command_node(self, node: CommandInvocationInitial) -> Tuple[CommandSignature, CommandInvocationInitial]:
        assert isinstance(node, CommandInvocationInitial)
        for signature in self.signature_loader.signatures:
            if signature.matches_command(node):
                return (signature, node)
        # raise ValueError(f'No matching signature found for command {node.cmd_name if node.cmd_name != "xargs" else "xargs_" + node.operand_list[0].name}')
        logging.warning(f'No matching signature found for command {node.cmd_name if node.cmd_name != "xargs" else "xargs_" + node.operand_list[0].name}')
        return (self.signature_loader.get_unknown_sigature(), node)
        

    def parse_pipeline(self) -> List[Tuple[CommandSignature, CommandInvocationInitial]]:
        assert len(self.ast) == 1
        pipe_node = self.ast[0][0]
        assert(isinstance(pipe_node, PipeNode))
        
        commands_in_pipe : list[CommandInvocationInitial] = []
        for command_node in pipe_node.items:
            assert (isinstance(command_node, CommandNode))
            cmd_raw = command_node.pretty()
            commands_in_pipe.append(annot_parse(cmd_raw))
        
        return [self.parse_command_node(command) for command in commands_in_pipe]
