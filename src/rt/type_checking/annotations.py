from dataclasses import dataclass
from enum import StrEnum, auto


class CommandAnnotationKind(StrEnum):
    ASSUME = auto()  # The command's input is guaranteed to match this regex
    ASSERT = auto()  # The command's output must be a subset of this regex
    EXPECT = auto()  # Like ASSERT but anchored line-at-a-time (stored, not yet checked)
    INPUT = auto()  # The pipeline's initial stdin matches this regex (e.g. heredoc)
    OUTPUT = (
        auto()
    )  # The pipeline's final stdout matches this regex (treated like ASSERT on the last command)


class EnvAnnotationKind(StrEnum):
    VAR = auto()  # The value of environment variable $var matches this regex
    FILE = auto()  # The content of a file operand matches this regex
    CONCRETIZE = auto()  # The annotation was produced by reading and analyzing a file
    INPUT_CONTAINS = "assert_contains"
    # ^ matches the annotation keyword `# @assert_contains` in shell comments.
    # The value is explicit (not auto()) so the parser can use it as a lookup key.
    # Semantics: a command's input must contain strings matching this regex.
    OUTPUT_CONTAINS = (
        auto()
    )  # The pipeline's final output must contain strings matching this regex


@dataclass(frozen=True)
class CommandAnnotation:
    kind: CommandAnnotationKind
    regex: str


@dataclass(frozen=True)
class EnvAnnotation:
    kind: EnvAnnotationKind
    regex: str
