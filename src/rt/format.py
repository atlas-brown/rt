import json
from collections.abc import Sequence

from rt.automaton_to_regex import automaton_summary, automaton_to_regex
from rt.regular_types.stream_type import StreamType
from rt.shell.parser import Pipeline
from rt.type_checking.checker import (
    AssertionViolationError,
    HeuristicViolationError,
    InputMismatchError,
    TypeCheckError,
)


def format_human(errors: Sequence[TypeCheckError], pipeline: Pipeline) -> str:
    commands = [inv.cmd_name for inv, _ in pipeline.commands]
    lines: list[str] = []

    for error in errors:
        match error:
            case InputMismatchError(
                cmd_idx=idx, actual=actual, expected=expected, witness=witness
            ):
                consumer = commands[idx] if idx < len(commands) else "?"
                producer = commands[idx - 1] if idx > 0 else "?"
                frag = _pipe_fragment(commands, max(0, idx - 1), idx + 1)
                ln = _line_number(pipeline, max(0, idx - 1))
                lines.append(f"Error (ln. {ln}):")
                lines.append(f"> {frag}")
                lines.append(
                    f"  {producer} produced '{_pretty(actual)}' "
                    f"but {consumer} expects '{_pretty(expected)}'"
                )
                if witness:
                    lines.append(f'  Counterexample: "{witness}"')

            case AssertionViolationError(
                cmd_idx=idx, output=output, asserted=asserted, witness=witness
            ):
                cmd = commands[idx] if idx < len(commands) else "?"
                frag = _pipe_fragment(commands, idx, idx + 1)
                ln = _line_number(pipeline, idx)
                lines.append(f"Error (ln. {ln}):")
                lines.append(f"> {frag}")
                lines.append(
                    f"  {cmd} produced '{_pretty(output)}' "
                    f"but asserted '{asserted}'"
                )
                if witness:
                    lines.append(f'  Counterexample: "{witness}"')

            case HeuristicViolationError(cmd_idx=idx, message=msg):
                ln = _line_number(pipeline, idx)
                frag = _pipe_fragment(commands, idx, idx + 1)
                lines.append(f"Warning (ln. {ln}):")
                lines.append(f"> {frag}")
                lines.append(f"  {msg}")

            case _:
                lines.append(str(error))

        lines.append("")

    return "\n".join(lines).rstrip()


def format_json(errors: Sequence[TypeCheckError], pipeline: Pipeline) -> str:
    commands = [inv.cmd_name for inv, _ in pipeline.commands]
    result: list[dict] = []

    for error in errors:
        entry: dict = {}

        match error:
            case InputMismatchError(
                cmd_idx=idx, actual=actual, expected=expected, witness=witness
            ):
                entry.update(
                    kind="input_mismatch",
                    cmd_idx=idx,
                    actual=_pretty(actual),
                    expected=_pretty(expected),
                    witness=witness,
                )
            case AssertionViolationError(
                cmd_idx=idx, output=output, asserted=asserted, witness=witness
            ):
                entry.update(
                    kind="assertion_violation",
                    cmd_idx=idx,
                    output=_pretty(output),
                    asserted=asserted,
                    witness=witness,
                )
            case HeuristicViolationError(cmd_idx=idx, message=msg):
                entry.update(
                    kind="heuristic_violation",
                    cmd_idx=idx,
                    command=commands[idx] if idx < len(commands) else "?",
                    message=msg,
                )
            case _:
                entry.update(kind="unknown", error=str(error))

        result.append(entry)

    return json.dumps(result, indent=2)


def format_compact(errors: Sequence[TypeCheckError], pipeline: Pipeline) -> str:
    commands = [inv.cmd_name for inv, _ in pipeline.commands]
    lines: list[str] = []

    for error in errors:
        match error:
            case InputMismatchError(
                cmd_idx=idx, actual=actual, expected=expected, witness=witness
            ):
                consumer = commands[idx] if idx < len(commands) else "?"
                producer = commands[idx - 1] if idx > 0 else "?"
                ln = _line_number(pipeline, max(0, idx - 1))
                lines.append(
                    f"Error (ln. {ln}): {producer} -> {consumer}: "
                    f"'{_pretty(actual)}' does not match '{_pretty(expected)}'"
                )
            case AssertionViolationError(
                cmd_idx=idx, output=output, asserted=asserted, witness=witness
            ):
                cmd = commands[idx] if idx < len(commands) else "?"
                ln = _line_number(pipeline, idx)
                lines.append(
                    f"Error (ln. {ln}): {cmd}: "
                    f"output '{_pretty(output)}' does not match assertion '{asserted}'"
                )
            case HeuristicViolationError(cmd_idx=idx, message=msg):
                ln = _line_number(pipeline, idx)
                lines.append(f"Warning (ln. {ln}): {msg}")
            case _:
                lines.append(str(error))

    return "\n".join(lines)


def _line_number(pipeline: Pipeline, cmd_idx: int) -> str:
    items = pipeline.ast.items if pipeline.ast else []
    if cmd_idx < len(items):
        return str(getattr(items[cmd_idx], "line_number", "?"))
    return "?"


def _pipe_fragment(commands: Sequence[str], start: int, end: int) -> str:
    return " | ".join(commands[start:end])


def _pretty(st: StreamType) -> str:
    if st.regex is not None:
        return st.regex
    regex = automaton_to_regex(st.automaton)
    if regex is not None:
        return regex
    return automaton_summary(st.automaton)
