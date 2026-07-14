from dataclasses import dataclass
from enum import StrEnum, auto

# @assume_input <command> : <regex>    the command's input is the regex (no checking, trust)
# @assume_output <command> : <regex>   the command's output is the regex (no checking, trust)
# @assert_input <command> : <regex>    the command's input is a subset of the regex (checked)
# @assert_output <command> : <regex>   the command's output is a subset of the regex (checked)
# @assert_input_contains <command> : <regex>   the command's input is a superset of the regex (checked)
# @assert_output_contains <command> : <regex>  the command's output is a superset of the regex (checked)

# Arrow fallback forms (disambiguated in parser, never stored as these kinds):
# @assume <regex> -> <command>          alt for assume_input
# @assume <command> -> <regex>          alt for assume_output
# @assert <regex> -> <command>          alt for assert_input
# @assert <command> -> <regex>          alt for assert_output
# @assert_contains <regex> -> <command> alt for assert_input_contains
# @assert_contains <command> -> <regex> alt for assert_output_contains

# @var <name> : <regex>         describes the contents of the given variable
# @file <name> : <regex>        describes the contents of the given file
# @concretize <name> : <path>   read the file at path and use its contents as the type


class CommandAnnotationKind(StrEnum):
    ASSUME_INPUT = auto()
    ASSUME_OUTPUT = auto()
    ASSERT_INPUT = auto()
    ASSERT_OUTPUT = auto()
    ASSERT_INPUT_CONTAINS = auto()
    ASSERT_OUTPUT_CONTAINS = auto()


class EnvAnnotationKind(StrEnum):
    VAR = auto()
    FILE = auto()
    CONCRETIZE = auto()


@dataclass(frozen=True)
class CommandAnnotation:
    kind: CommandAnnotationKind
    command_str: str
    regex: str


@dataclass(frozen=True)
class EnvAnnotation:
    kind: EnvAnnotationKind
    name: str
    regex: str
