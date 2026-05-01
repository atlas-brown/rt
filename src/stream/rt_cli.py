#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from typing import Iterable


from stream.type_checker import ErrorResult, ScriptChecker
from stream.utils.format import pretty_ast_node


INPUT_MISMATCH_RE = re.compile(
    r"Input type '(?P<actual>.*?)' is not compatible with expected input "
    r"'(?P<expected>.*?)' for command",
    re.DOTALL,
)
OUTPUT_EMPTY_RE = re.compile(r"Output type '(?P<actual>.*?)' is empty for command", re.DOTALL)
SIMPLE_SELF_LOOP_RE = re.compile(
    r"RegularType\(Automaton\).*?state 0 \[accept\]:\s*(?P<label>[^\n]+?) -> 0\s*$",
    re.DOTALL,
)


def _strip_regular_type(type_text: str | None) -> str:
    if not type_text:
        return "unknown"
    type_text = type_text.strip()
    self_loop_match = SIMPLE_SELF_LOOP_RE.search(type_text)
    if self_loop_match:
        return f"[{self_loop_match.group('label').strip()}]*"
    if type_text.startswith("RegularType(") and type_text.endswith(")"):
        inner = type_text[len("RegularType("):-1]
        if "\n" not in inner:
            return inner
    if "\n" in type_text:
        return " ".join(line.strip() for line in type_text.splitlines() if line.strip())
    return type_text


def _escape_witness(witness: str) -> str:
    return (
        witness
        .replace("\t", "\\t")
        .replace("\n", "\\n")
        .replace('"', '\\"')
    )


def _pipe_fragment(commands: list[str], start: int, end: int) -> str:
    fragment = " | ".join(commands[start:end])
    if end < len(commands):
        fragment += " | ..."
    return fragment


def _error_kind(error: ErrorResult) -> str:
    message = error.message or ""
    if INPUT_MISMATCH_RE.search(message):
        return "input"
    if OUTPUT_EMPTY_RE.search(message):
        return "empty"
    return "other"


def _input_mismatch_lines(error: ErrorResult, pipe_node) -> list[str]:
    commands = [pretty_ast_node(command) for command in pipe_node.items]
    consumer_index = max(0, min((error.command_index or 1) - 1, len(commands) - 1))
    producer_index = max(0, consumer_index - 1)
    match = INPUT_MISMATCH_RE.search(error.message or "")
    actual = _strip_regular_type(match.group("actual") if match else None)
    expected = _strip_regular_type(match.group("expected") if match else None)
    line_number = getattr(pipe_node.items[producer_index], "line_number", "?")

    lines = [
        f"Error (ln. {line_number}):",
        f"> {_pipe_fragment(commands, producer_index, min(consumer_index + 1, len(commands)))}",
        f"  {commands[producer_index]} > {actual}",
        "maybe incompatible w/",
        f"  {commands[consumer_index]} > {expected}",
    ]
    if error.witness is not None:
        lines.append(f'Counterexample: "{_escape_witness(error.witness)}"')
    return lines


def _empty_output_lines(error: ErrorResult, pipe_node) -> list[str]:
    commands = [pretty_ast_node(command) for command in pipe_node.items]
    command_index = max(0, min((error.command_index or 1) - 1, len(commands) - 1))
    if error.command_name:
        for index, command in enumerate(commands):
            if command.split(maxsplit=1)[0] == error.command_name:
                command_index = index
                break

    match = OUTPUT_EMPTY_RE.search(error.message or "")
    actual = _strip_regular_type(match.group("actual") if match else None)
    line_number = getattr(pipe_node.items[command_index], "line_number", "?")

    return [
        f"Error (ln. {line_number}):",
        f"> {_pipe_fragment(commands, command_index, min(command_index + 1, len(commands)))}",
        f"  {commands[command_index]} > {actual}",
        "has empty output",
    ]


def _fallback_lines(error: ErrorResult, pipe_node) -> list[str]:
    line_number = getattr(pipe_node.items[0], "line_number", "?") if pipe_node.items else "?"
    lines = [f"Error (ln. {line_number}):", f"> {pretty_ast_node(pipe_node)}"]
    if error.message:
        lines.append(error.message)
    return lines


def format_error(error: ErrorResult, pipe_node) -> str:
    kind = _error_kind(error)
    if kind == "input":
        lines = _input_mismatch_lines(error, pipe_node)
    elif kind == "empty":
        lines = _empty_output_lines(error, pipe_node)
    else:
        lines = _fallback_lines(error, pipe_node)
    return "\n".join(lines)


def iter_formatted_errors(script_path: str) -> Iterable[str]:
    checker = ScriptChecker(script_path)
    for pipeline_index, result in enumerate(checker):
        pipe_node = checker.pipeline_nodes[pipeline_index]
        for error in result.error_results:
            yield format_error(error, pipe_node)
        if result.runtime_error_message:
            yield "\n".join([
                f"Error (ln. {getattr(pipe_node.items[0], 'line_number', '?')}):",
                f"> {pretty_ast_node(pipe_node)}",
                result.runtime_error_message,
            ])


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RT and print paper-style diagnostics.")
    parser.add_argument("script", help="Shell script to check")
    args = parser.parse_args()

    first_error = next(iter_formatted_errors(args.script), None)
    if first_error is None:
        print("No RT errors found.")
        return 0

    print(first_error)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
