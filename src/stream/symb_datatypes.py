from __future__ import annotations
import logging
from dataclasses import dataclass

from shasta.ast_node import (
    AndNode,
    AstNode,
    CaseNode,
    CommandNode,
    DefunNode,
    ForNode,
    IfNode,
    NotNode,
    OrNode,
    PipeNode,
    RedirectionNode,
    SemiNode,
    SubshellNode,
    WhileNode,
    BArgChar,
    BackgroundNode,
    QArgChar
)
# from shseer import reporter,error_report
    

@dataclass(frozen=True)
class RawNode:
    ast_node: AstNode
    rawtext: str
    line_before: int
    line_after: int


def traverse_node(nd : AstNode, pipelines_nodes : list[AstNode]):
    match nd:
        case CommandNode():
            for assig in nd.assignments:
                traverse_node(assig, pipelines_nodes)
            for ls_arg in nd.arguments:
                for arg in ls_arg:
                    if isinstance(arg,QArgChar):
                        for arg in arg.arg:
                            if isinstance(arg,BArgChar):
                                traverse_node(arg.node, pipelines_nodes)
                    if isinstance(arg,BArgChar):
                        traverse_node(arg.node, pipelines_nodes)
        case DefunNode():
            traverse_node(nd.body,pipelines_nodes)
        case IfNode():
            traverse_node(nd.cond, pipelines_nodes)
            traverse_node(nd.then_b, pipelines_nodes)
            traverse_node(nd.else_b, pipelines_nodes)
        case AndNode():
            traverse_node(nd.left_operand, pipelines_nodes)
            traverse_node(nd.right_operand, pipelines_nodes)
        case OrNode():
            traverse_node(nd.left_operand, pipelines_nodes)
            traverse_node(nd.right_operand, pipelines_nodes)
        case NotNode():
            traverse_node(nd.body, pipelines_nodes)
        case ForNode():
            traverse_node(nd.body, pipelines_nodes)
        case WhileNode():
            traverse_node(nd.test, pipelines_nodes)
            traverse_node(nd.body, pipelines_nodes)
        case CaseNode():
            for case in nd.cases:
                traverse_node(case["cbody"], pipelines_nodes)
        case PipeNode():
            pipelines_nodes.append(nd)
        case SemiNode():
            traverse_node(nd.left_operand, pipelines_nodes)
            traverse_node(nd.right_operand, pipelines_nodes)
        case SubshellNode():
            traverse_node(nd.body, pipelines_nodes)
        case BackgroundNode():
            traverse_node(nd.node, pipelines_nodes)
        case RedirectionNode():
            return
        case _:
            logging.debug(f"Node not handled: {nd}")
    

def get_pipe_nodes(ls : list[RawNode]) -> list[AstNode]:
    pipeline_nodes = []
    for nd in ls:
        traverse_node(nd.ast_node, pipeline_nodes)
    return pipeline_nodes
    