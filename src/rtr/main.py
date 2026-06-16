from __future__ import annotations

import argparse
import logging
import pathlib
import re
import sys
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal

from stream.config.global_config import CONFIG
from stream.parser.shell_parser_util import annot_parser_wrapper as parse_invocation
from stream.regular_type import RegularType
from stream.signature_loader import SignatureLoader
from stream.type_checker import ErrorResult, ScriptChecker
from stream.utils.format import pretty_ast_node


LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "DISABLED"]

INPUT_MISMATCH_RE = re.compile(
    r"Input type '(?P<actual>.*?)' is not compatible with expected input "
    r"'(?P<expected>.*?)' for command",
    re.DOTALL,
)
OUTPUT_EMPTY_RE = re.compile(
    r"Output type '(?P<actual>.*?)' is empty for command", re.DOTALL
)
SIMPLE_SELF_LOOP_RE = re.compile(
    r"RegularType\(Automaton\).*?state 0 \[accept\]:\s*(?P<label>[^\n]+?) -> 0\s*$",
    re.DOTALL,
)


@dataclass
class CommandResolution:
    invocation: str
    input_type: RegularType
    output_type: RegularType
    command_type: object


def cli_main() -> None:
    raise SystemExit(main_cli())


def main_cli(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in {"-h", "--help"}:
        _top_level_parser().print_help()
        return 0
    if args and args[0] == "check":
        return check_cli(args[1:])
    if args and args[0] in {"resolve", "type"}:
        return resolve_cli(args[1:])
    if _looks_like_check_invocation(args):
        return check_cli(args)
    return resolve_cli(args)


def _top_level_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rtr",
        description="Regular type checker and command type resolver.",
        epilog=(
            "Examples:\n"
            "  rtr check script.sh\n"
            "  rtr script.sh\n"
            "  rtr resolve -i '.*' grep foo\n"
            "  rtr grep foo"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["check", "resolve", "type"],
        help="Use 'check' for shell scripts or 'resolve' for one command.",
    )
    return parser


def _looks_like_check_invocation(args: list[str]) -> bool:
    if not args:
        return True
    if any(arg == "-i" or arg == "--input-type" or arg.startswith("--input-type=") for arg in args):
        return False
    first = args[0]
    if first.startswith("-"):
        return True
    path = pathlib.Path(first)
    return path.is_file() or path.suffix in {".sh", ".bash", ".zsh"} or "/" in first


def check_cli(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="rtr check",
        description="Run RT on a shell script and print the first diagnostic.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=pathlib.Path,
        help="Shell script to analyze; leave empty for interactive stdin use.",
    )
    parser.add_argument(
        "-d",
        "--disable-annotations",
        action="store_true",
        help="Ignore user-provided annotations.",
    )
    parser.add_argument(
        "-L",
        "--log-level",
        metavar="LEVEL",
        choices=LOG_LEVELS,
        default="DISABLED",
        help="Set the logging level (default: %(default)s).",
    )
    args = parser.parse_args(argv)
    if args.file is None:
        return interactive_check(args.disable_annotations, args.log_level)
    return check_file(args.file, args.disable_annotations, args.log_level)


def check_file(
    file: pathlib.Path,
    disable_annotations: bool = False,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "DISABLED"] = "DISABLED",
) -> int:
    configure_runtime(disable_annotations, log_level)
    first_error = next(
        iter_formatted_errors(
            file.resolve(strict=True).as_posix(),
            enable_user_annotations=not disable_annotations,
        ),
        None,
    )
    if first_error is None:
        print("No RT errors found.")
        return 0
    print(first_error)
    return 1


def interactive_check(
    disable_annotations: bool = False,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "DISABLED"] = "DISABLED",
) -> int:
    configure_runtime(disable_annotations, log_level)
    if sys.stdin.isatty():
        print("Reading pipelines from stdin; use Ctrl+D to exit")

    had_error = False
    while True:
        try:
            pipeline = input("> " if sys.stdin.isatty() else "")
        except EOFError:
            break
        if not pipeline:
            continue
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh") as temp_file:
            temp_file.write(pipeline)
            temp_file.flush()
            first_error = next(
                iter_formatted_errors(
                    temp_file.name,
                    enable_user_annotations=not disable_annotations,
                ),
                None,
            )
        if first_error is None:
            print("No RT errors found.")
        else:
            print(first_error)
            had_error = True
    return 1 if had_error else 0


def configure_runtime(disable_annotations: bool, log_level: str) -> None:
    level = logging.CRITICAL + 10 if log_level == "DISABLED" else getattr(logging, log_level)
    logging.basicConfig(level=level)
    CONFIG["enable_user_annotation"] = not disable_annotations


def resolve_cli(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="rtr resolve",
        description="Resolve the regular type of one command invocation.",
    )
    parser.add_argument(
        "-i",
        "--input-type",
        type=str,
        default=None,
        help="Regular type to use as the command input. Defaults to the command's expected input type.",
    )
    parser.add_argument(
        "--show-command-type",
        action="store_true",
        help="Print the command type AST used for output inference.",
    )
    parser.add_argument("command", type=str, help="Command name to resolve.")
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        type=str,
        help="Command invocation arguments.",
    )
    args = parser.parse_args(argv)
    input_type = RegularType(args.input_type) if args.input_type is not None else None
    resolution = resolve_command(args.command, args.args, input_type)
    print_resolution(resolution, show_command_type=args.show_command_type)
    return 0


def resolve_command(
    command: str,
    args: Sequence[str],
    input_type: RegularType | None = None,
) -> CommandResolution:
    invocation = parse_invocation([command, *args])
    signature = SignatureLoader.get_instance().load_signature(invocation.cmd_name)
    expected_input_type, _ = signature.determine_input_type(invocation, [], [], {})
    actual_input_type = input_type if input_type is not None else expected_input_type

    command_type = signature.determine_command_type(invocation, [], {})
    result = signature.apply_command_type(command_type, actual_input_type)
    return CommandResolution(
        invocation=" ".join((command, *args)),
        input_type=actual_input_type,
        output_type=result.output_type,
        command_type=command_type,
    )


def print_resolution(resolution: CommandResolution, show_command_type: bool = False) -> None:
    print("Invocation:")
    print(resolution.invocation)
    print()
    print("Type:")
    print(f"{regular_type_text(resolution.input_type)} -> {regular_type_text(resolution.output_type)}")
    if show_command_type:
        print()
        print("Command type:")
        print(resolution.command_type)


def regular_type_text(regular_type: RegularType) -> str:
    return regular_type.pattern if regular_type.pattern is not None else repr(regular_type)


def iter_formatted_errors(
    script_path: str,
    enable_user_annotations: bool = True,
) -> Iterable[str]:
    checker = ScriptChecker(script_path, enable_user_annotations=enable_user_annotations)
    for pipeline_index, result in enumerate(checker):
        if checker.pipeline_nodes is None or pipeline_index >= len(checker.pipeline_nodes):
            continue
        pipe_node = checker.pipeline_nodes[pipeline_index]
        for error in result.error_results:
            yield format_error(error, pipe_node)
        if result.runtime_error_message:
            yield "\n".join(
                [
                    f"Error (ln. {getattr(pipe_node.items[0], 'line_number', '?')}):",
                    f"> {pretty_ast_node(pipe_node)}",
                    result.runtime_error_message,
                ]
            )


def format_error(error: ErrorResult, pipe_node) -> str:
    kind = _error_kind(error)
    if kind == "input":
        lines = _input_mismatch_lines(error, pipe_node)
    elif kind == "empty":
        lines = _empty_output_lines(error, pipe_node)
    else:
        lines = _fallback_lines(error, pipe_node)
    return "\n".join(lines)


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


def _strip_regular_type(type_text: str | None) -> str:
    if not type_text:
        return "unknown"
    type_text = type_text.strip()
    self_loop_match = SIMPLE_SELF_LOOP_RE.search(type_text)
    if self_loop_match:
        return f"[{self_loop_match.group('label').strip()}]*"
    if type_text.startswith("RegularType(") and type_text.endswith(")"):
        inner = type_text[len("RegularType(") : -1]
        if "\n" not in inner:
            return inner
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


if __name__ == "__main__":
    cli_main()
