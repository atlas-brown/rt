# TODO(deferred): Implement hole mapping provider for StreamTypeTemplate.instantiate().
# During type checking, the checker must build a Mapping[str, Automaton] that maps
# each predefined hole name (corresponding to command input, positional arguments,
# and option arguments) to its inferred automaton. This mapping is then passed to
# StreamTypeTemplate.from_regex() and used during instantiation.

from abc import ABC
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass

import rt.regular_types.database.registry as types
from rt.regular_types.stream_type import StreamType
from rt.shell.parser import Pipeline
from rt.type_checking.annotations import (
    CommandAnnotationKind,
    EnvAnnotationKind,
)
from rt.type_checking.heuristics import CommandPosition, Context, Heuristic

# Collected once at import time.  If a Heuristic subclass is loaded after this
# module is first imported it will not be included.
_DEFAULT_HEURISTICS = Heuristic.__subclasses__()


@dataclass(frozen=True)
class TypeCheckError(ABC):
    pass


@dataclass(frozen=True)
class InputMismatchError(TypeCheckError):
    cmd_idx: int
    actual: StreamType
    expected: StreamType
    witness: str


@dataclass(frozen=True)
class AssertionViolationError(TypeCheckError):
    cmd_idx: int
    output: StreamType
    asserted: str
    witness: str


@dataclass(frozen=True)
class HeuristicViolationError(TypeCheckError):
    cmd_idx: int
    message: str


def type_check(
    pipeline: Pipeline,
    heuristics: Sequence[type[Heuristic]] = _DEFAULT_HEURISTICS,
) -> Iterator[TypeCheckError]:
    input = StreamType.from_pattern(".*")

    for i, (inv, anns) in enumerate(pipeline.commands):
        cmd_type = types.get_type(inv, anns, pipeline.env)

        assert_input = None
        for a in anns:
            if a.kind == CommandAnnotationKind.ASSERT_INPUT:
                assert_input = StreamType.from_pattern(a.regex)

        skip_input_check = any(
            a.kind == CommandAnnotationKind.ASSUME_INPUT for a in anns
        )

        accepted = assert_input if assert_input is not None else cmd_type.accepted_input
        if accepted is not None and not skip_input_check:
            is_subtype, witness = input.is_subtype(accepted, True)
            if not is_subtype:
                yield InputMismatchError(
                    cmd_idx=i,
                    actual=input,
                    expected=accepted,
                    witness=witness,
                )

        # TODO(deferred): Populate mapping
        mapping: Mapping[str, StreamType] = dict()
        output = cmd_type.apply(input, mapping)

        ctx = Context(
            inv=inv,
            typ=cmd_type,
            inp=input,
            out=output,
            pos=(
                CommandPosition.FIRST
                if i == 0
                else (
                    CommandPosition.LAST
                    if i == len(pipeline.commands) - 1
                    else CommandPosition.INBETWEEN
                )
            ),
        )

        skip_remaining_checks = False
        for h in heuristics:
            if h.is_violated(ctx):
                yield HeuristicViolationError(cmd_idx=i, message=h.message(ctx))

            # TODO(deferred): Is overriding the output and skipping remaining checks a good idea? Should the next heuristics also be skipped? What if the output gets overridden many times?
            if (tmp := h.output_override(ctx)) is not None:
                output = tmp
            if h.skip_remaining_checks(ctx):
                skip_remaining_checks = True

        if not skip_remaining_checks:
            for ann in anns:
                if ann.kind == CommandAnnotationKind.ASSERT_OUTPUT:
                    asserted = StreamType.from_pattern(ann.regex)
                    is_ok, witness = output.is_subtype(asserted, True)
                    if not is_ok:
                        yield AssertionViolationError(
                            cmd_idx=i,
                            output=output,
                            asserted=ann.regex,
                            witness=witness,
                        )
                elif ann.kind == CommandAnnotationKind.ASSERT_INPUT_CONTAINS:
                    asserted = StreamType.from_pattern(ann.regex)
                    is_ok, witness = asserted.is_subtype(input, True)
                    if not is_ok:
                        yield AssertionViolationError(
                            cmd_idx=i,
                            output=input,
                            asserted=ann.regex,
                            witness=witness,
                        )
                elif ann.kind == CommandAnnotationKind.ASSERT_OUTPUT_CONTAINS:
                    asserted = StreamType.from_pattern(ann.regex)
                    is_ok, witness = asserted.is_subtype(output, True)
                    if not is_ok:
                        yield AssertionViolationError(
                            cmd_idx=i,
                            output=output,
                            asserted=ann.regex,
                            witness=witness,
                        )

        input = output

    yield from _check_output_contains(pipeline, input)


def _resolve_input(pipeline: Pipeline) -> StreamType:
    if pipeline.commands:
        _, anns = pipeline.commands[0]
        for ann in anns:
            if ann.kind == CommandAnnotationKind.INPUT:
                return StreamType.from_pattern(ann.regex)
    return StreamType.from_pattern(".*")


def _check_output_contains(
    pipeline: Pipeline, output: StreamType
) -> Iterator[TypeCheckError]:
    # __stdout__ is a sentinel key used by the shell parser (parser.py) to group
    # OUTPUT_CONTAINS env annotations. The parser stores these under this key because
    # they apply to the pipeline's output stream rather than a specific variable.
    annotations = pipeline.env.get("__stdout__", [])
    for ann in annotations:
        if ann.kind == EnvAnnotationKind.OUTPUT_CONTAINS:
            asserted = StreamType.from_pattern(ann.regex)
            is_ok, _ = asserted.is_subtype(output, True)
            if not is_ok:
                yield AssertionViolationError(
                    cmd_idx=len(pipeline.commands) - 1,
                    output=output,
                    asserted=ann.regex,
                    witness="",
                )
