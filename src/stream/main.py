import argparse
import pathlib
import logging
from typing import Literal
import tempfile
from inspect import signature
from collections.abc import Iterator
import re
import sys


from stream.config.global_config import CONFIG
from stream.type_checker import ErrorResult, ScriptChecker
from stream.constants import readable_automata_repr
from stream.utils.format import pretty_ast_node


def cli_main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        nargs="?",
        type=pathlib.Path,
        help="The shell script to analyze; leave empty for interactive use",
    )
    parser.add_argument(
        "-d",
        "--disable-annotations",
        action="store_true",
        help="Ignore all user-provided annotations",
    )
    parser.add_argument(
        "-L",
        "--log-level",
        metavar="LEVEL",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "DISABLED"],
        default=signature(main).parameters["log_level"].default,  # Define like this to avoid duplication of the defaults
        help=f"Set the logging level to one of DEBUG, INFO, WARNING, ERROR, CRITICAL or DISABLED (default: %(default)s)",
    )
    readable_group = parser.add_mutually_exclusive_group()
    readable_group.add_argument(
        "--readable-types",
        dest="readable_types",
        action="store_true",
        default=True,
        help="Render automaton-backed regular types as readable regexes when possible.",
    )
    readable_group.add_argument(
        "--no-readable-types",
        dest="readable_types",
        action="store_false",
        help="Keep automaton-backed regular types in raw automaton form.",
    )

    args = parser.parse_args()
    if args.file:
        main(args.file, args.disable_annotations, args.log_level, args.readable_types)
    else:
        interactive_main(args.disable_annotations, args.log_level, args.readable_types)


def main(
    file: pathlib.Path,
    disable_annotations: bool = False,
    log_level: Literal[
        "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "DISABLED"
    ] = "DISABLED",
    readable_types: bool = True,
):
    preamble(disable_annotations, log_level)
    exit_code = check_pipeline(file.resolve(strict=True).as_posix(), readable_types)
    postamble()
    sys.exit(exit_code)


def interactive_main(
    disable_annotations: bool = signature(main)
    .parameters["disable_annotations"]
    .default,
    log_level: Literal[
        "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "DISABLED"
    ] = signature(main)
    .parameters["log_level"]
    .default,
    readable_types: bool = signature(main).parameters["readable_types"].default,
):
    preamble(disable_annotations, log_level)
    if sys.stdin.isatty():
        print("Reading pipelines from stdin; use Ctrl+D to exit")
    while True:
        try:
            if pipeline := input("> "):
                with tempfile.NamedTemporaryFile(suffix=".sh") as temp_file:
                    temp_file.write(pipeline.encode("utf-8"))
                    temp_file.flush()
                    check_pipeline(temp_file.name, readable_types)
        except EOFError:
            break
    postamble()


def preamble(
    disable_annotations: bool,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "DISABLED"],
) -> None:
    logging.basicConfig(level=getattr(logging, log_level.upper()) if log_level.upper() != "DISABLED" else logging.CRITICAL + 10)
    logging.info(
        "Annotations are %s", "enabled" if not disable_annotations else "disabled"
    )
    CONFIG["enable_user_annotation"] = not disable_annotations

    # Add any other main/interactive_main common setup here


def postamble() -> None:
    pass

    # Add any other main/interactive_main common cleanup here


# ----------------------------------------------


# Code taken from the artifact evaluation branch
def check_pipeline(file: str, readable_types: bool = True) -> int:
    first_error = next(iter_formatted_errors(file, readable_types=readable_types), None)
    if first_error is None:
        print("No RT errors found.")
        return 0

    print(first_error)
    return 1


INPUT_MISMATCH_RE = re.compile(
    r"Input type '(?P<actual>.*?)' is not compatible with expected input "
    r"'(?P<expected>.*?)' for command",
    re.DOTALL,
)
OUTPUT_EMPTY_RE = re.compile(
    r"Output type '(?P<actual>.*?)' is empty for command", re.DOTALL
)

def _strip_regular_type(type_text: str | None) -> str:
    if not type_text:
        return "unknown"
    type_text = type_text.strip()
    if type_text.startswith("RegularType(") and type_text.endswith(")"):
        inner = type_text[len("RegularType(") : -1]
        if "\n" not in inner:
            return inner
    if type_text.startswith("RegularType(Automaton)\n"):
        return type_text
    if "\n" in type_text:
        return " ".join(line.strip() for line in type_text.splitlines() if line.strip())
    return type_text


def _escape_witness(witness: str) -> str:
    return witness.replace("\t", "\\t").replace("\n", "\\n").replace('"', '\\"')


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
    line_number = (
        getattr(pipe_node.items[0], "line_number", "?") if pipe_node.items else "?"
    )
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


def iter_formatted_errors(
    script_path: str, *, readable_types: bool = True
) -> Iterator[str]:
    with readable_automata_repr(readable_types):
        checker = ScriptChecker(script_path)
        for pipeline_index, result in enumerate(checker):
            if checker.pipeline_nodes is None:
                continue
            pipe_node = checker.pipeline_nodes[pipeline_index]
            for error in result.error_results:
                yield format_error(error, pipe_node)
            if getattr(result, "runtime_error_message", None):
                yield "\n".join(
                    [
                        f"Error (ln. {getattr(pipe_node.items[0], 'line_number', '?')}):",
                        f"> {pretty_ast_node(pipe_node)}",
                        result.runtime_error_message,
                    ]
                )


if __name__ == "__main__":
    cli_main()
