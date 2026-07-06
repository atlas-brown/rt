import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Self, overload

from rt.constants import ALPHABET_AUTOMATON, NO_NEWLINE_AUTOMATON
from rt.java_api import Automaton, SpecialOperations
from rt.regex import Dialect, PosixClass, ast, parse_regex


@dataclass(frozen=True)
class StreamType:
    automaton: Automaton
    regex: str | None = None

    @classmethod
    def from_automaton(cls, automaton: Automaton) -> Self:
        return cls.from_automaton(
            automaton.intersection(ALPHABET_AUTOMATON).intersection(
                NO_NEWLINE_AUTOMATON
            )
        )

    @classmethod
    def from_regex(cls, regex: ast.Regex) -> Self:
        try:
            automaton = regex.to_automaton({})
        except ValueError:
            raise ValueError(
                f"{cls.__name__} cannot contain holes; use {StreamTypeTemplate.__name__} for that"
            )
        return cls.from_automaton(automaton)

    @classmethod
    def from_pattern(
        cls, pattern: str, dialect: Dialect = Dialect.ERE_EXTENDED
    ) -> Self:
        return cls.from_regex(parse_regex(pattern, dialect=dialect))

    @overload
    def is_subtype(self, other: Self, with_witness: Literal[False]) -> bool: ...

    @overload
    def is_subtype(
        self, other: Self, with_witness: Literal[True]
    ) -> tuple[bool, str]: ...

    def is_subtype(
        self, other: Self, with_witness: bool
    ) -> bool | tuple[bool, str | None]:
        a = self.automaton
        b = other.automaton
        is_subtype = a.subsetOf(b)

        if not with_witness:
            return is_subtype

        if is_subtype:
            return is_subtype, None

        witness = None
        diff = a.minus(b)
        print_diff = diff.intersection(PosixClass.PRINT.to_automaton())
        no_newline_diff = print_diff.intersection(NO_NEWLINE_AUTOMATON)
        if not no_newline_diff.isEmpty():
            witness = str(no_newline_diff.getShortestExample(True))
        elif not print_diff.isEmpty():
            witness = str(print_diff.getShortestExample(True))
        else:
            witness = str(diff.getShortestExample(True))

        escaped_witness = ""
        for c in witness:
            if c == "\n":
                escaped_witness += "\\n"
            elif c == "\t":
                escaped_witness += "\\t"
            elif c == "\r":
                escaped_witness += "\\r"
            else:
                escaped_witness += c

        return is_subtype, escaped_witness

    def is_empty(self) -> bool:
        return self.automaton.isEmpty()

    def is_empty_string(self) -> bool:
        return self.automaton.isEmptyString()

    def union(self, other: Self) -> Self:
        autom = self.automaton.union(other.automaton)
        return self.from_automaton(autom)

    def intersect(self, other: Self) -> Self:
        autom = self.automaton.intersection(other.automaton)
        return self.from_automaton(autom)

    def concatenate(self, other: Self) -> Self:
        autom = self.automaton.concatenate(other.automaton)
        return self.from_automaton(autom)

    def subtract(self, other: Self) -> Self:
        autom = self.automaton.minus(other.automaton)
        return self.from_automaton(autom)

    def complement(self) -> Self:
        autom = NO_NEWLINE_AUTOMATON.minus(self.automaton)
        return self.from_automaton(autom)

    def reverse(self) -> Self:
        autom = self.automaton.clone()
        SpecialOperations.reverse(autom)  # Mutates in-place
        return self.from_automaton(autom)

    def repeat(self, min: int, max: int | None) -> Self:
        if max is None:
            autom = self.automaton.repeat(min)
        else:
            autom = self.automaton.repeat(min, max)
        return self.from_automaton(autom)


@dataclass(frozen=True)
class StreamTypeTemplate:
    regex_ast: ast.Regex

    @classmethod
    def from_regex(cls, regex_ast: ast.Regex) -> Self:
        return cls(regex_ast)

    def instantiate(self, holes: Mapping[str, StreamType]) -> StreamType:
        automaton = self.regex_ast.to_automaton(
            {k: v.automaton for k, v in holes.items()}
        )
        return StreamType.from_automaton(automaton)
