import logging
from typing import Any, Dict, List, Tuple
from shasta.ast_node import *
import itertools as it

# Pipeline := PipeNode

def mutate(pipeline: 'Pipeline') -> 'iterator[Pipeline]':
    return it.chain(mutator_swap(pipeline),
                    mutator_drop(pipeline),
                    mutator_arg_drop(pipeline))

def mutator_swap(pipeline: 'Pipeline') -> 'iterator[Pipeline]':
    items = pipeline.items
    for i in range(len(items) - 1):
        new_items = items[:i] + [items[i+1], items[i]] + items[i+2:]
        yield PipeNode(pipeline.is_background, new_items)

def yield_drops(l):
    for i in range(len(l)):
        new = l.copy()
        del new[i]
        yield new

def mutator_drop(pipeline: 'Pipeline') -> 'iterator[Pipeline]':
    for new_items in yield_drops(pipeline.items):
        yield PipeNode(pipeline.is_background, new_items)

def mutator_arg_drop(pipeline: 'Pipeline') -> 'iterator[Pipeline]':
    def replace_cmd_args(cmd, new_args):
        return CommandNode(cmd.line_number,
                           cmd.assignments,
                           new_args,
                           cmd.redir_list)

    for i in range(len(pipeline.items)):
        cmd = pipeline.items[i]
        for new_args in yield_drops(cmd.arguments):
            new_items = pipeline.items[:i] + [replace_cmd_args(cmd, new_args)] + pipeline.items[i+1:]
            yield PipeNode(pipeline.is_background, new_items)


