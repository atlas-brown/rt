from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from enum import StrEnum, auto

from rt.java_api import Automaton


@dataclass(frozen=True)
class Regex(ABC):
    """Base class for all regex AST nodes."""

    @abstractmethod
    def to_automaton(self, holes: Mapping[str, Automaton]) -> Automaton:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    def has_child_of_type(self, t: type["Regex"]) -> bool:
        if isinstance(self, t):
            return True
        for field in fields(self):
            value = getattr(self, field.name)

            if isinstance(value, Sequence) and not isinstance(value, str):
                for item in value:
                    if isinstance(item, Regex) and item.has_child_of_type(t):
                        return True

            elif isinstance(value, Regex) and value.has_child_of_type(t):
                return True

        return False


@dataclass(frozen=True)
class EmptyLanguage(Regex):
    """The empty set - matches nothing."""

    def to_automaton(self, holes: Mapping[str, Automaton]) -> Automaton:
        return Automaton.makeEmpty()

    def __str__(self) -> str:
        return ""  # no regex syntax for the empty language


@dataclass(frozen=True)
class Epsilon(Regex):
    """The empty string - matches only the empty string."""

    def to_automaton(self, holes: Mapping[str, Automaton]) -> Automaton:
        return Automaton.makeEmptyString()

    def __str__(self) -> str:
        return ""


@dataclass(frozen=True)
class Literal(Regex):
    """A single literal character (e.g., `a`)."""

    char: str

    def __post_init__(self):
        if len(self.char) != 1:
            raise ValueError(
                f"{self.__class__.__name__} must contain exactly one character (got: '{self.char}')"
            )

    def to_automaton(self, holes: Mapping[str, Automaton]) -> Automaton:
        return Automaton.makeChar(self.char)

    def __str__(self) -> str:
        return _esc(self.char, _NORMAL_META_CHARS)


@dataclass(frozen=True)
class Dot(Regex):
    """A period (`.`) - matches any single character except a newline (`\\n`)."""

    def to_automaton(self, holes: Mapping[str, Automaton]) -> Automaton:
        return Automaton.makeAnyChar()

    def __str__(self) -> str:
        return "."


@dataclass(frozen=True)
class Concatenation(Regex):
    """A sequence of sub-expressions (e.g., `abc`)."""

    left: Regex
    right: Regex

    def to_automaton(self, holes: Mapping[str, Automaton]) -> Automaton:
        return self.left.to_automaton(holes).concatenate(self.right.to_automaton(holes))

    def __str__(self) -> str:
        prec = _PREC[type(self)]
        l = _str_child(self.left, prec)
        r = _str_child(self.right, prec)
        return f"{l}{r}"


@dataclass(frozen=True)
class Repetition(Regex):
    """A repeated expression (e.g., `a{1,3}`)."""

    regex: Regex
    min: int
    max: int | None

    def __post_init__(self):
        if self.min < 0 or (self.max is not None and self.max < 0):
            raise ValueError(
                f"{self.__class__.__name__} interval bounds must be non-negative (got: {{{self.min},{self.max or ''}}})"
            )

        if self.max is not None and self.min > self.max:
            raise ValueError(
                f"{self.__class__.__name__} lower bound must not be greater than the upper bound (got: {{{self.min},{self.max or ''}}})"
            )

    def to_automaton(self, holes: Mapping[str, Automaton]) -> Automaton:
        a = self.regex.to_automaton(holes)
        if self.max is not None:
            return a.repeat(self.min, self.max)
        return a.repeat(self.min)

    def __str__(self) -> str:
        # fmt: off
        c = _str_child(self.regex, _PREC[type(self)])
        match self.min, self.max:
            case 0, None:        c += "*"
            case 1, None:        c += "+"
            case 0, 1:           c += "?"
            case m, None:        c += f"{{{m},}}"
            case m, n if m == n: c += f"{{{m}}}"
            case m, n:           c += f"{{{m},{n}}}"
        return c
        # fmt: on


@dataclass(frozen=True)
class Range:
    """A character range inside a character class (e.g., `a-z`)."""

    start: str
    end: str

    def __post_init__(self):
        if len(self.start) > 1 or len(self.end) > 1:
            raise ValueError(
                f"{self.__class__.__name__} bounds must be exactly one character (got: '{self.start}-{self.end}')"
            )

        if self.start > self.end:
            raise ValueError(
                f"{self.__class__.__name__} bounds must be low-to-high (got: '{self.start}-{self.end}')"
            )


# https://pubs.opengroup.org/onlinepubs/9799919799/
class PosixClass(StrEnum):
    """A POSIX character class (e.g., `[:alpha:]`)."""

    ALNUM = auto()
    ALPHA = auto()
    BLANK = auto()
    CNTRL = auto()
    DIGIT = auto()
    GRAPH = auto()
    LOWER = auto()
    PRINT = auto()
    PUNCT = auto()
    SPACE = auto()
    UPPER = auto()
    XDIGIT = auto()

    def to_automaton(self) -> Automaton:
        # https://pubs.opengroup.org/onlinepubs/9799919799/
        # fmt: off
        match self:
            case PosixClass.ALNUM:  return _UPPER().union(_LOWER()).union(_DIGIT())
            case PosixClass.ALPHA:  return _UPPER().union(_LOWER())
            case PosixClass.BLANK:  return _BLANK()
            case PosixClass.CNTRL:  return _CNTRL()
            case PosixClass.DIGIT:  return _DIGIT()
            case PosixClass.GRAPH:  return _UPPER().union(_LOWER()).union(_DIGIT()).union(_PUNCT())
            case PosixClass.LOWER:  return _LOWER()
            case PosixClass.PRINT:
                return (
                    _UPPER()
                    .union(_LOWER())
                    .union(_DIGIT())
                    .union(_PUNCT())
                    .union(Automaton.makeChar(" "))
                )
            case PosixClass.PUNCT:  return _PUNCT()
            case PosixClass.SPACE:  return _SPACE()
            case PosixClass.UPPER:  return _UPPER()
            case PosixClass.XDIGIT: return _XDIGIT()
        # fmt: on


@dataclass(frozen=True)
class CharacterClass(Regex):
    """A character class (e.g., `[^abc]`)."""

    is_negated: bool
    items: Sequence[str | Range | PosixClass]

    def to_automaton(self, holes: Mapping[str, Automaton]) -> Automaton:
        autom = Automaton.makeEmpty()

        for item in self.items:
            if isinstance(item, PosixClass):
                autom = autom.union(item.to_automaton())
            if isinstance(item, Range):
                autom = autom.union(Automaton.makeCharRange(item.start, item.end))
            if isinstance(item, str):
                autom = autom.union(Automaton.makeCharSet(item))

        if self.is_negated:
            autom = Automaton.makeAnyChar().minus(autom)

        return autom

    def __str__(self) -> str:
        c = ""
        for i in self.items:
            # fmt: off
            match i:
                case PosixClass(): c += f"[:{i}:]"
                case Range(s, e):  c += f"{_esc(s, _CHAR_CLASS_META_CHARS)}-{_esc(e, _CHAR_CLASS_META_CHARS)}"
                case str(s):       c += _esc(s, _CHAR_CLASS_META_CHARS)
            # fmt: on
        return f"[{"^" if self.is_negated else ""}{c}]"


@dataclass(frozen=True)
class Intersection(Regex):
    """An intersection (e.g., `hello&ell`) - matches patterns matched by both the left and the right sub-expressions."""

    left: Regex
    right: Regex

    def to_automaton(self, holes: Mapping[str, Automaton]) -> Automaton:
        return self.left.to_automaton(holes).intersection(
            self.right.to_automaton(holes)
        )

    def __str__(self) -> str:
        prec = _PREC[type(self)]
        l = _str_child(self.left, prec)
        r = _str_child(self.right, prec)
        return f"{l}&{r}"


@dataclass(frozen=True)
class Complement(Regex):
    """A complement (e.g., `~a`)."""

    regex: Regex

    def to_automaton(self, holes: Mapping[str, Automaton]) -> Automaton:
        return Automaton.makeAnyString().minus(self.regex.to_automaton(holes))

    def __str__(self) -> str:
        c = _str_child(self.regex, _PREC[type(self)])
        return f"~{c}"


@dataclass(frozen=True)
class Union(Regex):
    """An alternation / union (e.g., `a|b`)."""

    left: Regex
    right: Regex

    def to_automaton(self, holes: Mapping[str, Automaton]) -> Automaton:
        return self.left.to_automaton(holes).union(self.right.to_automaton(holes))

    def __str__(self) -> str:
        prec = _PREC[type(self)]
        l = _str_child(self.left, prec)
        r = _str_child(self.right, prec)
        return f"{l}|{r}"


@dataclass(frozen=True)
class StartAnchor(Regex):
    """A start-of-string anchor (`^`)."""

    def to_automaton(self, holes: Mapping[str, Automaton]) -> Automaton:
        return Automaton.makeEmptyString()

    def __str__(self) -> str:
        return "^"


@dataclass(frozen=True)
class EndAnchor(Regex):
    """An end-of-string anchor (`$`)."""

    def to_automaton(self, holes: Mapping[str, Automaton]) -> Automaton:
        return Automaton.makeEmptyString()

    def __str__(self) -> str:
        return "$"


@dataclass(frozen=True)
class Hole(Regex):
    """
    A placeholder to be filled later (`{{name}}`) - used for creating templates,
    which can be instantiated by replacing all holes with new regular expressions.
    """

    name: str

    def to_automaton(self, holes: Mapping[str, Automaton]) -> Automaton:
        if self.name not in holes:
            raise ValueError("Hole name not present in mapping")
        return holes[self.name]

    def __str__(self) -> str:
        return f"{{{{{self.name}}}}}"


# Precendence of nodes for grouping
_PREC: dict[type[Regex], int] = defaultdict(
    lambda: 6,  # Default for all node types not present in the dict
    {
        Union: 1,
        Intersection: 2,
        Concatenation: 3,
        Repetition: 4,
        Complement: 5,
    },
)


def _str_child(child: Regex, parent_prec: int) -> str:
    prec = _PREC[type(child)]
    c = str(child)
    if prec < parent_prec:
        c = f"({c})"

    return c


# Character sets for regex escaping rules
_NORMAL_META_CHARS = "^$.*+?{}[]()|&~\\"
_CHAR_CLASS_META_CHARS = "\\]"


def _esc(char: str, meta_chars: str) -> str:
    return f"\\{char}" if char in meta_chars else char


_UPPER = lambda: Automaton.makeCharRange("A", "Z")  # "A-Z"
_LOWER = lambda: Automaton.makeCharRange("a", "z")  # "a-z"
_DIGIT = lambda: Automaton.makeCharRange("0", "9")  # "0-9"
_BLANK = lambda: Automaton.makeChar(" ").union(Automaton.makeChar("\t"))  # " \t"
_SPACE = (
    lambda: Automaton.makeChar(" ")
    .union(Automaton.makeChar("\t"))
    .union(Automaton.makeChar("\n"))
    .union(Automaton.makeChar("\v"))
    .union(Automaton.makeChar("\f"))
    .union(Automaton.makeChar("\r"))
)  # " \t\n\v\f\r"
_PUNCT = (
    lambda: Automaton.makeCharRange("!", "/")
    .union(Automaton.makeCharRange(":", "@"))
    .union(Automaton.makeCharRange("[", "`"))
    .union(Automaton.makeCharRange("{", "~"))
)  # "!-/:-@[-`{-~"
_XDIGIT = (
    lambda: Automaton.makeCharRange("0", "9")
    .union(Automaton.makeCharRange("A", "F"))
    .union(Automaton.makeCharRange("a", "f"))
)  # "0-9A-Fa-f"
_CNTRL = lambda: Automaton.makeCharRange("\x00", "\x1f").union(
    Automaton.makeChar("\x7f")
)  # "\x00-\x1f\x7f"
