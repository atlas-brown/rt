
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
    QArgChar,
    CArgChar,
    EArgChar,
    VArgChar,
    AArgChar
)

from shasta.json_to_ast import to_ast_node
import logging
import libdash.parser
import libdash
import os
import traceback
INITIALIZE_LIBDASH = True
## Parses straight a shell script to an AST
## through python without calling it as an executable
def parse_shell_to_asts(input_script_path : str):
    global INITIALIZE_LIBDASH
    try:
        if not os.path.isfile(input_script_path):
            raise libdash.parser.ParsingException(f"File {input_script_path} does not exist")
        logging.debug(f"Calling libdash parser initialization={INITIALIZE_LIBDASH} on {input_script_path}")
        new_ast_objects = libdash.parser.parse(input_script_path,init=INITIALIZE_LIBDASH)
        INITIALIZE_LIBDASH = False
        logging.debug(f"Finished libdash parser on {input_script_path}")
        ## Transform the untyped ast objects to typed ones
        new_ast_objects = list(new_ast_objects)
        logging.debug("Calling shasta")
        typed_ast_objects = []
        for (
            untyped_ast,
            original_text,
            linno_before,
            linno_after,
        ) in new_ast_objects:
            typed_ast = to_ast_node(untyped_ast)
            typed_ast_objects.append(
                (typed_ast, original_text, linno_before, linno_after)
            )
        logging.debug("Returning typed Shasta objects")
        return typed_ast_objects
    except Exception as e:
        logging.debug("Parsing error!", traceback.format_exc())


def traverse_node(nd : AstNode) -> list[PipeNode]:
    pipeline_nodes = []
    match nd:
        case CommandNode():
            for assig in nd.assignments:
                for val in assig.val:
                    pipeline_nodes += traverse_node(val)
            for ls_arg in nd.arguments:
                for arg in ls_arg:
                    pipeline_nodes += traverse_node(arg)
        case BArgChar():
            pipeline_nodes += traverse_node(nd.node)
        case QArgChar():
            for arg in nd.arg:
                pipeline_nodes += traverse_node(arg)
        case DefunNode():
            pipeline_nodes += traverse_node(nd.body)
        case IfNode():
            pipeline_nodes += traverse_node(nd.cond)
            pipeline_nodes += traverse_node(nd.then_b)
            pipeline_nodes += traverse_node(nd.else_b)
        case AndNode():
            pipeline_nodes += traverse_node(nd.left_operand)
            pipeline_nodes += traverse_node(nd.right_operand)
        case OrNode():
            pipeline_nodes += traverse_node(nd.left_operand)
            pipeline_nodes += traverse_node(nd.right_operand)
        case NotNode():
            pipeline_nodes += traverse_node(nd.body)
        case ForNode():
            pipeline_nodes += traverse_node(nd.body)
        case WhileNode():
            pipeline_nodes += traverse_node(nd.test)
            pipeline_nodes += traverse_node(nd.body)
        case CaseNode():
            for case in nd.cases:
                pipeline_nodes += traverse_node(case["cbody"])
        case PipeNode():
            pipeline_nodes.append(nd)
            for item in nd.items:
                pipeline_nodes += traverse_node(item)
        case SemiNode():
            pipeline_nodes += traverse_node(nd.left_operand)
            pipeline_nodes += traverse_node(nd.right_operand)
        case SubshellNode():
            pipeline_nodes += traverse_node(nd.body)
        case BackgroundNode():
            pipeline_nodes += traverse_node(nd.node)
        case RedirectionNode():
            pass
        case CArgChar() | EArgChar() | VArgChar() | AArgChar():
            pass
        case _:
            logging.debug(f"Node not handled: {type(nd)}")
    return pipeline_nodes

def extract_pipe_nodes_from_file(filename: str) -> list[PipeNode]:
    typed_ast_object = parse_shell_to_asts(filename)
    if typed_ast_object is None:
        return []
    pipeline_nodes = []
    for nd in typed_ast_object:
        pipeline_nodes += traverse_node(nd[0])
    return pipeline_nodes