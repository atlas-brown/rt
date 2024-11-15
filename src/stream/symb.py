
from shasta.ast_node import (
    AstNode,
)
from stream.shell_parser import parse_shell_to_asts
from stream.symb_datatypes import RawNode, get_pipe_nodes


def symb_engine(nodes: list[RawNode]) -> list[AstNode]:
    pipeline_nodes = get_pipe_nodes(nodes)
    return pipeline_nodes

def get_raw_nodes(filename) -> list[RawNode]:
    typed_ast_object = parse_shell_to_asts(filename)
    nodes = [RawNode(*x) for x in typed_ast_object]
    return nodes

def extract_pipe_nodes_from_file(file:str) -> list[AstNode]:
    nodes = get_raw_nodes(file)
    return symb_engine(nodes)