import json
from typing import Dict, List, Optional, Set
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
    AArgChar,
    RedirNode
)
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from pash_annotations.datatypes.BasicDatatypes import FlagOption, Flag, Option, Operand
from pash_annotations.parser.parser import get_dict_flag_to_primary_repr, get_dict_option_to_primary_repr, get_set_of_all_flags, get_set_of_all_options, are_all_individually_flags
from pash_annotations.parser.util_parser import get_json_data
from shasta.json_to_ast import to_ast_node
import logging
import libdash.parser
import libdash
import os
import traceback
import re
import tempfile
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
        case RedirectionNode() | RedirNode():
            pass
        case CArgChar() | EArgChar() | VArgChar() | AArgChar():
            pass
        case _:
            logging.debug(f"Node not handled: {type(nd)}")
    return pipeline_nodes


def filter_pipeline_nodes(filename: str, pipeline_nodes: list[PipeNode]) -> list[PipeNode]:
    script_content = []
    with open(filename) as f:
        for line in f:
            script_content.append(line)

    filtered_pipeline_nodes = []
    for node in pipeline_nodes:
        line_number = node.items[0].line_number
        if line_number < 2:
            continue
        # if the line above the command line is "# stream enable", then the pipeline will be extracted, otherwise it is ignored
        if script_content[line_number - 2].strip().startswith("#") and script_content[line_number - 2].replace("#", "").strip().lower() == "stream enable":
            filtered_pipeline_nodes.append(node)

    return filtered_pipeline_nodes

def extract_pipelines_from_string(filename: str) -> list[tuple[PipeNode, int]]:
    """
    Extract pipelines from a script by finding '# stream enable' comments
    and parsing only the pipeline sections that follow them.
    
    Returns:
        A list of tuples (pipeline_node, enable_line_number) where pipeline_node is the
        parsed PipeNode and enable_line_number is the line number of the 
        "# stream enable" comment that preceded it.
    """
    script_content = []
    with open(filename) as f:
        script_content = f.readlines()
    
    enable_pattern = re.compile(r'^\s*#\s*stream\s+enable\s*$')
    pipeline_nodes_with_lines = []
    
    # Find all "# stream enable" lines
    for i in range(len(script_content)):
        if enable_pattern.match(script_content[i]):
            # For each "# stream enable" found, process it independently
            pipeline_node = extract_single_pipeline(script_content, i)
            if pipeline_node:
                # Store both the pipeline node and the enable line number
                pipeline_nodes_with_lines.append((pipeline_node, i))
    
    return pipeline_nodes_with_lines

def extract_single_pipeline(script_content: list[str], enable_line_index: int) -> Optional[PipeNode]:
    """
    Extract a single pipeline following a "# stream enable" comment.
    Each pipeline is parsed independently in its own temporary file.
    
    Args:
        script_content: The entire script as a list of lines
        enable_line_index: The index of the "# stream enable" line
        
    Returns:
        The first PipeNode found in the pipeline, or None if no pipeline was found
    """
    # Found a stream enable line, the pipeline starts on the next line
    start_line = enable_line_index + 1
    if start_line >= len(script_content):
        return None  # No more lines after stream enable
    
    # Extract pipeline content
    pipeline_lines = []
    current_line = start_line
    
    # Always read at least one line
    if current_line < len(script_content):
        pipeline_lines.append(script_content[current_line])
        current_line += 1
    
    # Continue reading lines if they end with \ or | or start with #
    while current_line < len(script_content):
        prev_line = script_content[current_line - 1].strip()
        current_line_text = script_content[current_line].strip()
        
        # Continue if previous line ends with \ or | or current line starts with #
        if prev_line.endswith('\\') or prev_line.endswith('|') or current_line_text.startswith('#'):
            pipeline_lines.append(script_content[current_line])
            current_line += 1
        else:
            break
    
    # Extract the pipeline as a string
    pipeline_str = ''.join(pipeline_lines)
    
    # Create a dedicated temporary file for this specific pipeline
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_file:
        temp_file.write(pipeline_str)
        temp_file.flush()
        temp_file_path = temp_file.name
    
    try:
        # Parse only this specific pipeline's temporary file
        parsed_nodes = parse_shell_to_asts(temp_file_path)
        if parsed_nodes and len(parsed_nodes) > 0:
            # Extract pipeline nodes from the parsed AST for this specific pipeline
            pipe_nodes = traverse_node(parsed_nodes[0][0])
            # Return the first PipeNode from this specific extracted pipeline
            for node in pipe_nodes:
                if isinstance(node, PipeNode):
                    return node
    finally:
        # Clean up the temporary file for this pipeline
        os.unlink(temp_file_path)
    
    return None

def extract_pipe_nodes_from_file(filename: str, extract_all_pipelines: bool = True) -> list[PipeNode] | list[tuple[PipeNode, int]]:
    if not extract_all_pipelines:
        # Use string matching to find and extract pipelines
        # Return both the pipeline nodes and their enable line numbers
        return extract_pipelines_from_string(filename)
    
    # Original approach for extract_all_pipelines=True
    typed_ast_object = parse_shell_to_asts(filename)
    if typed_ast_object is None:
        return []
    pipeline_nodes: list[PipeNode] = []
    for nd in typed_ast_object:
        pipeline_nodes += traverse_node(nd[0])

    return pipeline_nodes


def string_of_arg(args):
    i = 0
    text = []
    while i < len(args):
        if isinstance(args[i],str):
            text.append(args[i])
            i = i+1
            continue
        c = args[i].pretty(quote_mode=0)
        if c == "$" and (i+1 < len(args)) and isinstance(args[i+1],EArgChar):
            c = "\\$"
        text.append(c)

        i = i+1
    
    text = "".join(text)

    return text

def annot_parser_wrapper(str_ls_args: list[str]) -> CommandInvocationInitial:

    # split all terms (command, flags, options, arguments, operands)
    parsed_elements_list : list[str] = str_ls_args

    cmd_name: str = parsed_elements_list[0]
    # Check if command annotation exists in extra_annotations directory
    extra_annotation_path = f'./src/stream/extra_annotations/{cmd_name}.json'
    if os.path.isfile(extra_annotation_path):
        # FIXME: ls.json is not complete
        with open(extra_annotation_path, 'r') as file:
            json_data = json.load(file)
    else:
        json_data = get_json_data(cmd_name)
    # TODO: if there is an element "\n", we lose the quotation marks currently

    set_of_all_flags: Set[str] = get_set_of_all_flags(json_data)
    dict_flag_to_primary_repr: Dict[str, str] = get_dict_flag_to_primary_repr(json_data)
    set_of_all_options: Set[str] = get_set_of_all_options(json_data)
    dict_option_to_primary_repr: Dict[str, str] = get_dict_option_to_primary_repr(json_data)
    # dict_option_to_class_for_arg: Dict[str, WhichClassForArg] = get_dict_option_to_class_for_arg(json_data)

    # parse list of command invocation terms
    flag_option_list: List[FlagOption] = []
    i = 1
    while i < len(parsed_elements_list):
        potential_flag_or_option = parsed_elements_list[i]
        if potential_flag_or_option in set_of_all_flags:
            flag_name_as_string: str = dict_flag_to_primary_repr.get(potential_flag_or_option, potential_flag_or_option)
            flag: Flag = Flag(flag_name_as_string)
            flag_option_list.append(flag)
        elif (potential_flag_or_option in set_of_all_options) and ((i+1) < len(parsed_elements_list)):
            option_name_as_string: str = dict_option_to_primary_repr.get(potential_flag_or_option, potential_flag_or_option)
            option_arg_as_string: str = parsed_elements_list[i+1]
            option = Option(option_name_as_string, option_arg_as_string)
            flag_option_list.append(option)
            i += 1  # since we consumed another term for the argument
        elif are_all_individually_flags(potential_flag_or_option, set_of_all_flags):
            for split_el in list(potential_flag_or_option[1:]):
                flag: Flag = Flag(f'-{split_el}')
                flag_option_list.append(flag)
        else:
            break  # next one is Operand, and we keep these in separate list
        i += 1

    # we would probably want to skip '--' but then the unparsed command could have a different meaning so we'd need to keep it
    # for now, omitted
    # if parsed_elements_list[i] == '--':
    #     i += 1

    # operand_list = [Operand(operand_name) for operand_name in parsed_elements_list[i:]]
    operand_list = []
    idx_list = []
    for idx in range(i,len(parsed_elements_list)):
        operand_list.append(Operand(parsed_elements_list[idx]))
        idx_list.append(idx)

    return CommandInvocationInitial(cmd_name, flag_option_list, operand_list)

def process_special_cases_in_args(s: list[str]) -> list[str]:
    if len(s) > 0:
        # handle special cases: head -1 -> head -n 1, tail -1 -> tail -n 1
        if s[0] in {"head", "tail"}:
            s2 = [s[0]]
            for arg in s[1:]:
                if arg.startswith("-") and arg[1:].isdigit():
                    s2.append("-n")
                    s2.append(arg[1:])
                else:
                    s2.append(arg)
            s = s2
        
        # handle special cases: du -ha -> du -h -a
        s2 = [s[0]]
        for arg in s[1:]:
            if arg.startswith("-") and len(arg) > 1:
                arg = arg[1:]
                while len(arg) > 1 and arg[:2].isalpha():
                    s2.append("-" + arg[0])
                    arg = arg[1:]
                s2.append("-" + arg)
            else:
                s2.append(arg)
        s = s2
        

        # handle special cases: cut -d/ -> cut -d /, cut -f1 -> cut -f 1
        s2 = [s[0]]
        for arg in s[1:]:
            if arg.startswith("-") and len(arg) > 2 and arg[1].isalpha() and not arg[2].isalpha():
                s2.append(arg[0:2])
                s2.append(arg[2:])
            else:
                s2.append(arg)

        s = s2

        # FIXME: correctly handle quoted arguments
        # provisional solution: remove quotes
        s2 = []
        for arg in s:
            if (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
                s2.append(arg[1:-1])
            else:
                s2.append(arg)
        s = s2
    return s

def string_of_ls_args(args) -> list[str]:
    s : list[str] = []
    for idx, a in enumerate(args):
        x = string_of_arg(a)
        s.append(x)
    return process_special_cases_in_args(s)

def get_command_invocation(cnd: CommandNode) -> CommandInvocationInitial:
    try:
        str_ls_args = string_of_ls_args(cnd.arguments)
        return  annot_parser_wrapper(str_ls_args)
    except Exception:
        logging.warning(f"Failed to parse command: {cnd.pretty()}")
    return CommandInvocationInitial("unknown", [], [])