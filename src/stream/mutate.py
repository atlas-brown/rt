import logging
from typing import Any, Dict, List, Tuple
from shasta.ast_node import *
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
import itertools as it

# Pipeline := List[CommandInvocationInitial]

def mutate(pipeline: 'Pipeline') -> 'iterator[Pipeline]':
    return it.chain(mutator_swap(pipeline),
                    mutator_drop(pipeline),
                    mutator_arg_drop(pipeline))

def mutator_swap(pipeline: 'Pipeline') -> 'iterator[Pipeline]':
    for i in range(len(pipeline) - 1):
        yield pipeline[:i] + [pipeline[i+1], pipeline[i]] + pipeline[i+2:]

def yield_drops(l):
    for i in range(len(l)):
        new = l.copy()
        del new[i]
        yield new

def mutator_drop(pipeline: 'Pipeline') -> 'iterator[Pipeline]':
    return yield_drops(pipeline)

def mutator_arg_drop(pipeline: 'Pipeline') -> 'iterator[Pipeline]':
    def replace_cmd_args(cmd, new_args):
        c = cmd.copy()
        c.operand_list = new_args
        return c

    for i in range(len(pipeline)):
        cmd = pipeline[i]
        for new_args in yield_drops(cmd.operand_list):
            yield pipeline[:i] + [replace_cmd_args(cmd, new_args)] + pipeline[i+1:]


