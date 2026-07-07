import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal, Self, overload

from rt.constants import ALPHABET_AUTOMATON, ALPHABET_SIZE, NO_NEWLINE_AUTOMATON
from rt.java_api import Automaton, SpecialOperations
from rt.regex import Dialect, PosixClass, ast, parse_regex
from rt.transducer import (
    compression_transducer,
    correct_cut_field_transducer,
    cut_char_transducer,
    first_regex_replacement_transducer,
    global_regex_extract_transducer,
    global_regex_replacement_transducer,
    product_transducer_automaton,
    start_regex_extract_transducer,
    start_regex_replacement_transducer,
    translation_transducer,
)
from rt.utils import char_set_complement


@dataclass(frozen=True)
class StreamType:
    automaton: Automaton
    regex: str | None = None

    @classmethod
    def from_automaton(cls, automaton: Automaton) -> Self:
        return cls(
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

    def replace(
        self, pattern: str | Self, replacement: str, first_occurence_only: bool
    ) -> Self:
        pattern_str = pattern if isinstance(pattern, str) else None
        pattern = self._compile_pattern(pattern)

        if (
            pattern_str is not None
            and (s1 := _find_exact_match(pattern_str)) is not None
        ):
            fst = (
                first_replacement_FST(s1, replacement)  # type: ignore
                if first_occurence_only
                else global_replacement_FST(s1, replacement)  # type: ignore
            )
            dfa = product_transducer_automaton(fst, self.automaton)
            return self.from_automaton(dfa)

        if pattern_str is not None:
            if pattern_str.startswith("^") and pattern_str.endswith("$"):
                fst = start_regex_replacement_transducer(
                    self._compile_pattern(".*").automaton, replacement
                )
                inner = self.intersect(pattern)
                outer = self.subtract(pattern)
                dfa = product_transducer_automaton(fst, inner.automaton)
                return self.from_automaton(automaton=dfa).union(outer)
            elif pattern_str.startswith("^"):
                fst = start_regex_replacement_transducer(pattern.automaton, replacement)
                dfa = product_transducer_automaton(fst, self.automaton)
                return self.from_automaton(dfa)
            elif pattern_str.endswith("$"):
                end_pattern = pattern_str[:-1]
                compiled_end = self._compile_pattern(end_pattern)
                rev_automaton = compiled_end.reverse().automaton
                fst = start_regex_replacement_transducer(
                    rev_automaton, replacement[::-1]
                )
                rev_input = self.reverse()
                dfa = product_transducer_automaton(fst, rev_input.automaton)
                return self.from_automaton(automaton=dfa).reverse()

        fst = (
            first_regex_replacement_transducer(pattern.automaton, replacement)
            if first_occurence_only
            else global_regex_replacement_transducer(pattern.automaton, replacement)
        )
        dfa = product_transducer_automaton(fst, self.automaton)
        return self.from_automaton(dfa)

    def match(self, pattern: str | Self) -> Self:
        pattern_str = pattern if isinstance(pattern, str) else None
        pattern = self._compile_pattern(pattern)

        if pattern_str is not None and _find_exact_match(pattern_str) is not None:
            has_match = self.intersect(
                self._compile_pattern(".*")
                .concatenate(pattern)
                .concatenate(self._compile_pattern(".*"))
            )
            if has_match.automaton.isEmpty():
                return self.from_automaton(automaton=Automaton.makeEmpty())
            return pattern

        if pattern_str is not None:
            if pattern_str.startswith("^") and pattern_str.endswith("$"):
                return self.intersect(pattern)
            elif pattern_str.startswith("^"):
                fst = start_regex_extract_transducer(pattern.automaton)
                dfa = product_transducer_automaton(fst, self.automaton)
                return self.from_automaton(dfa)
            elif pattern_str.endswith("$"):
                fst = start_regex_extract_transducer(pattern.reverse().automaton)
                rev_input = self.reverse()
                dfa = product_transducer_automaton(fst, rev_input.automaton)
                return self.from_automaton(automaton=dfa).reverse()

        fst = global_regex_extract_transducer(pattern.automaton)
        dfa = product_transducer_automaton(fst, self.automaton)
        return self.from_automaton(dfa)

    def translate_chars(
        self, source_chars: str, target_chars: str, invert: bool, squeeze: bool
    ) -> Self:
        source = _preprocess_char_set(source_chars)
        target = _preprocess_char_set(target_chars)
        if invert:
            if (inverted := char_set_complement(source, 0, ALPHABET_SIZE)) == "":
                raise ValueError(
                    f"Invalid set for tr: '{source}'; its complement is empty"
                )
            source = inverted

        fst = translation_transducer(source, target)
        dfa = product_transducer_automaton(fst, self.automaton)
        if squeeze:
            fst = compression_transducer(target)
            dfa = product_transducer_automaton(fst, dfa)
        return self.from_automaton(dfa)

    def extract_fields(
        self, separator: str, indices: Sequence[int], complement: bool
    ) -> Self:
        if not indices:
            return self._compile_pattern(".*")

        indices_list = list(indices)
        has_upperbound = True
        if indices_list and indices_list[-1] == -1:
            has_upperbound = False
            indices_list = indices_list[:-1]

        if complement:
            if not has_upperbound:
                return self._compile_pattern(".*")
            selected = set(indices_list)
            if not selected:
                return self._compile_pattern(".*")
            max_index = max(selected)
            indices_list = [i for i in range(1, max_index + 1) if i not in selected]
            indices_list.append(max_index + 1)
            has_upperbound = False

        if separator:
            fst = correct_cut_field_transducer(
                separator[-1], indices_list, has_upperbound
            )
        else:
            fst = cut_char_transducer(indices_list, has_upperbound)

        dfa = product_transducer_automaton(fst, self.automaton)
        return self.from_automaton(dfa)

    @classmethod
    def _compile_pattern(cls, pattern: str | Self) -> Self:
        if isinstance(pattern, str):
            ast = parse_regex(pattern)
            autom = ast.to_automaton({})
            autom = autom.intersection(ALPHABET_AUTOMATON)
            autom = autom.intersection(NO_NEWLINE_AUTOMATON)
            return cls.from_automaton(autom)
        return pattern


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


def _find_exact_match(
    regex: str | ast.Regex, dialect: Dialect = Dialect.ERE_EXTENDED
) -> str | None:
    """Extract a literal string from a regex pattern if it represents a "pure string", i.e., it matches only that string."""

    if isinstance(regex, str):
        regex = parse_regex(regex, dialect)

    if isinstance(regex, ast.Literal):
        return regex.char
    elif (
        isinstance(regex, ast.Concatenation)
        and (l := _find_exact_match(regex.left)) is not None
        and (r := _find_exact_match(regex.right)) is not None
    ):
        return l + r
    elif (
        isinstance(regex, ast.CharacterClass)
        and not regex.is_negated
        and len(regex.items) == 1
        and isinstance(regex.items[0], str)
    ):
        return regex.items[0]
    return None


def _preprocess_char_set(source_chars: str) -> str:
    """Expand a character set string for use in translation operations (like tr).

    Expands POSIX character classes (e.g. ``[:alpha:]``), character ranges
    (e.g. ``a-z``), and escape sequences into a flat string of literal characters.
    Dashes at the start or end of the set are treated as literal dash characters.
    Invalid ranges where the start character exceeds the end character raise ValueError.
    """
    source_chars = _replace_posix_class(source_chars)
    processed_chars = ""
    contains_dash = False
    i = 0
    if source_chars and source_chars[0] == "-":
        processed_chars += "-"
        i = 1

    while i < len(source_chars):
        if source_chars[i] == "-" and i > 0 and i < len(source_chars) - 1:
            start = source_chars[i - 1]
            end = source_chars[i + 1]
            if ord(start) > ord(end):
                raise ValueError(f"invalid range: {start}-{end}")
            else:
                for char_code in range(ord(start), ord(end) + 1):
                    if chr(char_code) == "-":
                        contains_dash = True
                    else:
                        processed_chars += chr(char_code)
            i += 1
        elif source_chars[i] == "-" and i == len(source_chars) - 1:
            contains_dash = True
        else:
            processed_chars += source_chars[i]
        i += 1

    if contains_dash:
        processed_chars += "-"

    processed_chars = _process_escape_chars(processed_chars)
    return processed_chars


def _replace_posix_class(source_chars: str) -> str:
    source_chars = source_chars.replace("[:lower:]", "a-z")
    source_chars = source_chars.replace("[:upper:]", "A-Z")
    source_chars = source_chars.replace("[:alpha:]", "a-zA-Z")
    source_chars = source_chars.replace("[:punct:]", "!-/:-@[-`{-~")
    source_chars = source_chars.replace("[:digit:]", "0-9")
    source_chars = source_chars.replace("[:alnum:]", "a-zA-Z0-9")
    source_chars = source_chars.replace("[:blank:]", " \t")
    source_chars = source_chars.replace("[:word:]", "a-zA-Z0-9_")
    source_chars = source_chars.replace("[:xdigit:]", "0-9a-fA-F")
    source_chars = source_chars.replace("[:space:]", " \t\n\r\f\v")
    return source_chars


def _process_escape_chars(source_chars: str) -> str:
    source_chars = source_chars.replace("\\\\", "\\")
    escape_dict = {
        "n": "\n",
        "t": "\t",
        "r": "\r",
        "v": "\v",
        "f": "\f",
        "b": "\b",
        "s": " ",
        "+": "+",
        "{": "{",
        "}": "}",
        "|": "|",
        "&": "&",
        "~": "~",
        "*": "*",
        "?": "?",
        ".": ".",
        "^": "^",
        "$": "$",
        "(": "(",
        ")": ")",
        "[": "[",
        "]": "]",
        '"': '"',
        "'": "'",
        "-": "-",
        "\\": "\\",
    }
    source_chars = re.sub(
        r'\\([\\ntrvfbs+{}|&~*?.^$()[\]"\']|-)',
        lambda m: escape_dict[m.group(1)],
        source_chars,
    )
    return source_chars
