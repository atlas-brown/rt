from contextlib import contextmanager

from stream.java_api import RegExp
from stream.regex_parser import RegexParser, ast_to_automaton

alphabet_size = 255

no_newline_automaton = ast_to_automaton(RegexParser("[^\\n]*").parse())
alphabet_automaton = RegExp(f"[{chr(0)}-{chr(alphabet_size)}]*").toAutomaton()

READABLE_AUTOMATA_REPR_ENABLED = False


def set_readable_automata_repr_enabled(enabled: bool) -> None:
    global READABLE_AUTOMATA_REPR_ENABLED
    READABLE_AUTOMATA_REPR_ENABLED = enabled


def get_readable_automata_repr_enabled() -> bool:
    return READABLE_AUTOMATA_REPR_ENABLED


@contextmanager
def readable_automata_repr(enabled: bool):
    previous = get_readable_automata_repr_enabled()
    set_readable_automata_repr_enabled(enabled)
    try:
        yield
    finally:
        set_readable_automata_repr_enabled(previous)
