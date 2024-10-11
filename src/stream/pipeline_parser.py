from typing import Any, Dict, List, Tuple
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

    def parse_shell_script(self) -> List[Any]:
        return parse_shell_to_asts(self.pipeline_address)

    def parse_command_node(self, node: CommandNode) -> Dict[str, Any]:
        assert isinstance(node, CommandNode)
        # command_parts = list(map(lambda part: "".join(part), node))

        for signature in self.signature_loader.signatures:
            if signature.matches_command(node):
                parsed_flags, parsed_args = signature.extract_flags_and_args(node)
                return {
                    "command_name": signature.command_name,
                    "signature": signature,
                    "parsed_flags": parsed_flags,
                    "parsed_args": parsed_args
                }
        print(node)
        raise ValueError(f"No matching signature found for command '{' '.join(node)}'.")

    def parse_pipeline(self) -> List[Dict[str, Any]]:
        assert len(self.ast) == 1
        pipe_node = self.ast[0][0]
        assert(isinstance(pipe_node, PipeNode))
        
        commands_in_pipe : list[CommandInvocationInitial] = []
        for command_node in pipe_node.items:
            assert (isinstance(command_node, CommandNode))
            cmd_raw = command_node.pretty()
            commands_in_pipe.append(annot_parse(cmd_raw))
        
        print(commands_in_pipe)
        return [self.parse_command_node(command) for command in commands_in_pipe]
        
        
        
        # pipe_str = self.ast[0][0]
        # print(pipe_str)
        # # need to be refined!!!!!!!!!!!
        # # pipeline_commands = [['seq', '2', '10'], ['grep', 'grep']]
        # # pipeline_commands = [['seq', '2', '10'], ['grep', 'grep'], ['xargs', '-n', '1', 'expr', '1', '+']]

        # return [self.parse_command_node(command) for command in pipeline_commands]
