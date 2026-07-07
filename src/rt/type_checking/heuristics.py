from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import ClassVar

from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from rt.regular_types.command_type import CommandType
from rt.regular_types.stream_type import StreamType


class CommandPosition(Enum):
    FIRST = auto()
    LAST = auto()
    INBETWEEN = auto()


@dataclass(frozen=True)
class Context:
    inv: CommandInvocationInitial
    typ: CommandType
    inp: StreamType
    out: StreamType
    pos: CommandPosition


@dataclass(frozen=True)
class Heuristic(ABC):
    name: ClassVar[str]

    @staticmethod
    @abstractmethod
    def is_violated(ctx: Context) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def message(ctx: Context) -> str:
        pass

    @staticmethod
    def output_override(ctx: Context) -> StreamType | None:
        return None

    @staticmethod
    def skip_remaining_checks(ctx: Context) -> bool:
        return False


@dataclass(frozen=True)
class NoEmptyOutput(Heuristic):
    name = "no_empty_output"

    @staticmethod
    def is_violated(ctx: Context) -> bool:
        return (
            ctx.pos != CommandPosition.LAST
            and ctx.out.is_empty()
            or ctx.out.is_empty_string()
        )

    @staticmethod
    def message(ctx: Context) -> str:
        return f"'{ctx.inv.cmd_name}' always produces empty output"

    @staticmethod
    def output_override(ctx: Context) -> StreamType | None:
        return StreamType.from_pattern(".*")

    @staticmethod
    def skip_remaining_checks(ctx: Context) -> bool:
        return True


class NoIgnoredInput(Heuristic):
    name = "no_ignored_input"

    @staticmethod
    def is_violated(ctx: Context) -> bool:
        return ctx.pos != CommandPosition.FIRST and ctx.typ.accepted_input is None

    @staticmethod
    def message(ctx: Context) -> str:
        return f"'{ctx.inv.cmd_name}' does not read from stdin"


class NoUselessComposition(Heuristic):
    name = "no_useless_composition"

    @staticmethod
    def is_violated(ctx: Context) -> bool:
        return ctx.inp.is_subtype(ctx.out, False) and ctx.out.is_subtype(ctx.inp, False)

    @staticmethod
    def message(ctx: Context) -> str:
        return f"'{ctx.inv.cmd_name}' does not transform its input"


class NoLexicographicNumericSort(Heuristic):
    name = "no_lexicographic_numeric_sort"

    @staticmethod
    def is_violated(ctx: Context) -> bool:
        NUMERIC_INPUT = StreamType.from_pattern(r"-?[0-9]+([ \t]*-?[0-9]+)*")
        return (
            ctx.inv.cmd_name == "sort"
            and "-n" not in {f.get_name() for f in ctx.inv.flag_option_list}
            and ctx.inp.is_subtype(NUMERIC_INPUT, False)
        )

    @staticmethod
    def message(ctx: Context) -> str:
        return (
            f"'sort' receives numeric input but the -n flag was not provided; "
            "sorting will be lexicographic"
        )
