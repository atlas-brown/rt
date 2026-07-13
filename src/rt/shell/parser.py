import json
import logging
import os
import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, overload

import libdash.parser
from pash_annotations.datatypes.BasicDatatypes import Flag, FlagOption, Operand, Option
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from pash_annotations.parser.parser import (
    are_all_individually_flags,
    get_dict_flag_to_primary_repr,
    get_dict_option_to_primary_repr,
    get_set_of_all_flags,
    get_set_of_all_options,
)
from pash_annotations.parser.util_parser import get_json_data
from shasta import ast_node as ast
from shasta import ast_walker as walker
from shasta.json_to_ast import to_ast_node

from rt.constants import EXTRA_PASH_ANNOTATIONS_DIR
from rt.type_checking.annotations import (
    CommandAnnotation,
    CommandAnnotationKind,
    EnvAnnotation,
    EnvAnnotationKind,
)

# TODO: Add naive flag/option/positional parsing when the pash parser fails

@dataclass(frozen=True)
class Pipeline:
    commands: Sequence[tuple[CommandInvocationInitial, Sequence[CommandAnnotation]]]
    env: Mapping[str, Sequence[EnvAnnotation]]
    ast: ast.PipeNode


@overload
def parse_pipelines(script: str) -> Iterator[Pipeline]: ...


@overload
def parse_pipelines(script: Path) -> Iterator[Pipeline]: ...


def parse_pipelines(script: str | Path) -> Iterator[Pipeline]:
    if isinstance(script, str):
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".sh", delete=False
        ) as tmp_file:
            tmp_file.write(script)
            tmp_file.flush()
            yield from _parse_pipelines(Path(tmp_file.name))
    else:
        yield from _parse_pipelines(script)


def _parse_pipelines(script: Path) -> Iterator[Pipeline]:
    script_lines: list[str] = script.read_text().splitlines()

    for node, _, _, _ in _parse_shell_script(script):
        for pipeline_node in _extract_pipeline_nodes(node):
            pipeline_items = list(pipeline_node.items)
            # TODO(deferred): What about non-CommandNode nodes? What if a pipeline is piping to a while for example? Maybe we should just exit with an error
            cmd_invocations = [
                _get_command_invocation(cmd)
                for cmd in pipeline_items
                if isinstance(cmd, ast.CommandNode)
            ]
            cmd_annotations: list[list[CommandAnnotation]] = [
                [] for _ in cmd_invocations
            ]
            env_annotations: dict[str, list[EnvAnnotation]] = {}

            line_number = next(
                (
                    it.line_number
                    for it in pipeline_items
                    if isinstance(it, ast.CommandNode)
                ),
                1,
            )

            while True:
                line_number -= 1  # Move one line up
                if line_number < 1:
                    break

                match = _ANNOTATION_PATTERN.match(
                    script_lines[line_number - 1]
                )  # Minus one for the list index
                if match is None:
                    break

                if match.group(1) is not None:
                    kind = match.group(1)
                    first = match.group(2)
                    second = match.group(3)

                    if kind in (
                        CommandAnnotationKind.ASSUME,
                        CommandAnnotationKind.ASSERT,
                        CommandAnnotationKind.EXPECT,
                    ):
                        if kind == CommandAnnotationKind.EXPECT:
                            pattern = first
                            command = second
                        else:
                            pattern = second
                            command = first

                        refined_command = _refine_command(command.replace(r"\"", '"'))
                        for i, cmd_node in enumerate(pipeline_items):
                            if (
                                isinstance(cmd_node, ast.CommandNode)
                                and cmd_node.pretty() == refined_command
                            ):
                                kind = CommandAnnotationKind(kind)
                                cmd_annotations[i].append(
                                    CommandAnnotation(kind, pattern)
                                )
                                break

                    elif kind == EnvAnnotationKind.INPUT_CONTAINS:
                        command = first
                        pattern = second
                        refined_command = _refine_command(command.replace(r"\"", '"'))
                        ann = EnvAnnotation(EnvAnnotationKind.INPUT_CONTAINS, pattern)
                        env_annotations.setdefault(refined_command, []).append(ann)

                elif match.group(4) is not None:
                    var = _normalize_annotation_var(match.group(5))
                    file_path = match.group(6)
                    concrete_pattern = _concretize_file_to_pattern(file_path, script)
                    ann = EnvAnnotation(EnvAnnotationKind.CONCRETIZE, concrete_pattern)
                    env_annotations.setdefault(var, []).append(ann)

                elif match.group(7) is not None:
                    kind = match.group(7)
                    pattern = match.group(8)

                    if kind == CommandAnnotationKind.INPUT:
                        cmd_annotations[0].append(
                            CommandAnnotation(CommandAnnotationKind.INPUT, pattern)
                        )
                    elif kind == CommandAnnotationKind.OUTPUT:
                        cmd_annotations[-1].append(
                            CommandAnnotation(CommandAnnotationKind.OUTPUT, pattern)
                        )
                    elif kind == EnvAnnotationKind.OUTPUT_CONTAINS:
                        ann = EnvAnnotation(EnvAnnotationKind.OUTPUT_CONTAINS, pattern)
                        env_annotations.setdefault("__stdout__", []).append(ann)

                elif match.group(9) is not None:
                    kind = match.group(9)
                    name = _normalize_annotation_var(match.group(10))
                    pattern = match.group(11)
                    kind = EnvAnnotationKind(kind)
                    ann = EnvAnnotation(kind, pattern)
                    env_annotations.setdefault(name, []).append(ann)

            command_pairs = [
                (inv, tuple(anns))
                for inv, anns in zip(cmd_invocations, cmd_annotations)
            ]

            yield Pipeline(
                commands=command_pairs,
                env=env_annotations,
                ast=pipeline_node,
            )


_LIBDASH_INITIALIZED = False

_DOUBLE_QUOTED_KINDS = "|".join(
    [
        CommandAnnotationKind.ASSUME,
        CommandAnnotationKind.ASSERT,
        CommandAnnotationKind.EXPECT,
        EnvAnnotationKind.INPUT_CONTAINS,
    ]
)

_SINGLE_QUOTED_KINDS = "|".join(
    [
        CommandAnnotationKind.INPUT,
        CommandAnnotationKind.OUTPUT,
        EnvAnnotationKind.OUTPUT_CONTAINS,
    ]
)

_COLON_KINDS = "|".join(
    [
        EnvAnnotationKind.FILE,
        EnvAnnotationKind.VAR,
    ]
)

_ANNOTATION_PATTERN = re.compile(
    rf'^\s*#\s*@({_DOUBLE_QUOTED_KINDS})\s*"(.*)"\s*-->\s*"(.*)"\s*$'
    rf'|^\s*#\s*@({EnvAnnotationKind.CONCRETIZE})\s*"(.*)"\s*-->\s*"(.*)"\s*$'
    rf'|^\s*#\s*@({_SINGLE_QUOTED_KINDS})\s*"(.*)"\s*$'
    rf'|^\s*#\s*@({_COLON_KINDS})\s*"(.*)"\s*:\s*"(.*)"\s*$'
)


def _normalize_annotation_var(var: str) -> str:
    return re.sub(r"\$(?!\{)([A-Za-z_][A-Za-z0-9_]*|[0-9]+)", r"${\1}", var)


def _parse_shell_script(
    script: Path,
) -> list[tuple[ast.AstNode, str | None, Any, Any]]:
    global _LIBDASH_INITIALIZED
    untyped_nodes = libdash.parser.parse(
        script.resolve(strict=True).as_posix(), init=not _LIBDASH_INITIALIZED
    )
    _LIBDASH_INITIALIZED = True

    typed_nodes: list[tuple[ast.AstNode, str | None, Any, Any]] = []
    for untyped_node, original_text, linno_before, linno_after in untyped_nodes:
        typed_node = to_ast_node(untyped_node)
        typed_nodes.append((typed_node, original_text, linno_before, linno_after))
    return typed_nodes


def _refine_command(cmd: str) -> str:
    with NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".sh") as tmp_file:
        tmp_file.write(cmd)
        tmp_file.flush()
        ast_nodes = _parse_shell_script(Path(tmp_file.name))
        if not ast_nodes:
            return cmd
        return ast_nodes[0][0].pretty()


def _extract_pipeline_nodes(node: ast.AstNode) -> list[ast.PipeNode]:
    pipeline_nodes: list[ast.PipeNode] = []
    walker.walk_ast_node(
        node,
        visit=lambda node: (
            pipeline_nodes.append(node) if isinstance(node, ast.PipeNode) else None
        ),
    )
    return pipeline_nodes


def _get_command_invocation(cmd: ast.CommandNode) -> CommandInvocationInitial:
    try:
        args = _args_to_strs(cmd.arguments)
        return _annot_parser_wrapper(args)
    except Exception:
        logging.warning(f"Failed to parse command: {cmd.pretty()}")
    return CommandInvocationInitial("unknown", [], [])


def _args_to_strs(args: Sequence[Sequence[ast.ArgChar]]) -> list[str]:
    s = [_arg_to_str(a) for a in args]
    return _process_special_cases_in_args(s)


def _arg_to_str(arg: Sequence[ast.ArgChar]):
    i = 0
    text: list[str] = []
    while i < len(arg):
        if isinstance((a := arg[i]), str):
            text.append(a)
            i = i + 1
            continue
        c = arg[i].pretty()
        if c == "$" and (i + 1 < len(arg)) and isinstance(arg[i + 1], ast.EArgChar):
            c = "\\$"
        text.append(c)
        i = i + 1
    return "".join(text)


def _process_special_cases_in_args(s: list[str]) -> list[str]:
    """Normalize command-line arguments so annotation strings match parsed invocations.

    Handles shell aliases, shorthand options, and quoting conventions:
    strips ``command``/`\\`/``_`` prefixes, expands ``head``/``tail`` short-options,
    splits clustered single-letter flags, rewrites ``egrep`` to ``grep -E``,
    strips ``--color=`` from grep, and removes surrounding quotes.
    """
    if len(s) > 0:
        if s[0] == "command" and len(s) > 1:
            s = s[1:]
        if s[0].startswith("\\") and len(s[0]) > 1:
            s[0] = s[0][1:]
        if s[0].startswith("_") and len(s[0]) > 1:
            s[0] = s[0][1:]
        if s[0] in {"head", "tail"}:
            s2 = [s[0]]
            for arg in s[1:]:
                if arg.startswith("-") and arg[1:].isdigit():
                    s2.append("-n")
                    s2.append(arg[1:])
                else:
                    s2.append(arg)
            s = s2
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
        s2 = [s[0]]
        for arg in s[1:]:
            if (
                arg.startswith("-")
                and len(arg) > 2
                and arg[1].isalpha()
                and not arg[2].isalpha()
            ):
                s2.append(arg[0:2])
                s2.append(arg[2:])
            else:
                s2.append(arg)
        s = s2
        if "_" in s[0]:
            s[0] = s[0].replace("_", "_-")
            s2 = s[0].split("_")
            s2.extend(s[1:])
            s = s2
        if s[0] == "egrep":
            s2 = ["grep", "-E"]
            s2.extend(s[1:])
            s = s2
        if s[0] == "grep":
            s2 = [s[0]]
            for arg in s[1:]:
                if not arg.startswith("--color="):
                    s2.append(arg)
            s = s2
        s2 = []
        for arg in s:
            if (arg.startswith('"') and arg.endswith('"')) or (
                arg.startswith("'") and arg.endswith("'")
            ):
                s2.append(arg[1:-1])
            else:
                s2.append(arg)
        s = s2
    return s


# TODO: This function is almost verbatim a copy-paste of the one in pash_annotations. Try to figure out a way to eliminate this duplication. The reason for this is the use of extra annotations that are local to this project.
def _annot_parser_wrapper(args: list[str]) -> CommandInvocationInitial:
    parsed_elements_list: list[str] = args
    cmd_name: str = parsed_elements_list[0]

    extra_annotation_path = EXTRA_PASH_ANNOTATIONS_DIR / f"{cmd_name}.json"
    if extra_annotation_path.is_file():
        with open(extra_annotation_path, "r") as file:
            json_data = json.load(file)
    else:
        json_data = get_json_data(cmd_name)

    set_of_all_flags = get_set_of_all_flags(json_data)
    dict_flag_to_primary_repr = get_dict_flag_to_primary_repr(json_data)
    set_of_all_options = get_set_of_all_options(json_data)
    dict_option_to_primary_repr = get_dict_option_to_primary_repr(json_data)

    flag_option_list: list[FlagOption] = []
    i = 1
    while i < len(parsed_elements_list):
        potential_flag_or_option = parsed_elements_list[i]
        if potential_flag_or_option in set_of_all_flags:
            flag_name_as_string = dict_flag_to_primary_repr.get(
                potential_flag_or_option, potential_flag_or_option
            )
            flag = Flag(flag_name_as_string)
            flag_option_list.append(flag)
        elif (potential_flag_or_option in set_of_all_options) and (
            (i + 1) < len(parsed_elements_list)
        ):
            option_name_as_string = dict_option_to_primary_repr.get(
                potential_flag_or_option, potential_flag_or_option
            )
            option_arg_as_string = parsed_elements_list[i + 1]
            option = Option(option_name_as_string, option_arg_as_string)
            flag_option_list.append(option)
            i += 1
        elif are_all_individually_flags(potential_flag_or_option, set_of_all_flags):
            for split_el in list(potential_flag_or_option[1:]):
                flag = Flag(f"-{split_el}")
                flag_option_list.append(flag)
        else:
            break
        i += 1

    operand_list = [
        Operand(parsed_elements_list[idx])
        for idx in range(i, len(parsed_elements_list))
    ]
    return CommandInvocationInitial(cmd_name, flag_option_list, operand_list)


def _escape_concrete_line(line: str) -> str:
    escaped: list[str] = []
    special_chars = set(r"\|&~*+?.^$()[]{}")
    for char in line:
        if char == "\t":
            escaped.append(r"\t")
        elif char == "\r":
            escaped.append(r"\r")
        elif char in special_chars:
            escaped.append("\\" + char)
        else:
            escaped.append(char)
    return "".join(escaped)


def _concretize_file_to_pattern(path: str, script_dir: Path) -> str:
    file_path = path
    if not os.path.isabs(file_path):
        file_path = os.path.join(str(script_dir.parent), file_path)

    with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
        lines = handle.read().splitlines()

    seen: set[str] = set()
    escaped_lines: list[str] = []
    for line in lines:
        if line in seen:
            continue
        seen.add(line)
        escaped_lines.append(_escape_concrete_line(line))

    if not escaped_lines:
        return ""
    if len(escaped_lines) == 1:
        return escaped_lines[0]
    return "(" + "|".join(escaped_lines) + ")"
