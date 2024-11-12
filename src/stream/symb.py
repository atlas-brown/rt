import json
import logging
import os
import sys
import traceback
from argparse import ArgumentParser
from copy import deepcopy
from dataclasses import dataclass
from typing import Optional

from pash_annotations.datatypes.BasicDatatypes import FlagOption, Operand
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from pash_annotations.parser.parser import parse as annot_parse
from shasta.ast_node import (
    AndNode,
    ArgChar,
    AstNode,
    CArgChar,
    CaseNode,
    CommandNode,
    DefunNode,
    DupRedirNode,
    FileRedirNode,
    ForNode,
    HeredocRedirNode,
    IfNode,
    NotNode,
    OrNode,
    PipeNode,
    RedirNode,
    SemiNode,
    SubshellNode,
    WhileNode,
)
from stream.shell_parser import parse_shell_to_asts
from stream.symb_datatypes import NodeMap, RawNode, check_traversal, traverse_raw_nodes
from typing import Set, Literal, List, Dict

from pash_annotations.datatypes.BasicDatatypes import FlagOption, Flag, Option, Operand, FileName, ArgStringType
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from pash_annotations.parser.util_parser import get_json_data
from pash_annotations.parser.parser import get_dict_flag_to_primary_repr, get_dict_option_to_primary_repr, get_set_of_all_flags, get_set_of_all_options, are_all_individually_flags

def symb_engine(nodes: list[RawNode]) -> list[AstNode]:
    pipeline_nodes = traverse_raw_nodes(nodes)
    return pipeline_nodes

def get_raw_nodes(filename) -> list[RawNode]:
    typed_ast_object = parse_shell_to_asts(filename)
    nodes = [RawNode(*x) for x in typed_ast_object]
    return nodes

def nodes_from_file(file:str) -> list[AstNode]:
    nodes = get_raw_nodes(file)
    return symb_engine(nodes)