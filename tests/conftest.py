from collections.abc import Callable, Mapping

import pytest

from rt.constants import ALPHABET_AUTOMATON
from rt.java_api import Automaton
from rt.regex.ast import Regex
from rt.regex.parser import Dialect, parse_regex


@pytest.fixture(scope="session")
def parse():
    def _parse(pattern: str, dialect: Dialect = Dialect.ERE_EXTENDED) -> Regex:
        return parse_regex(pattern, dialect=dialect)

    return _parse


@pytest.fixture(scope="session")
def unparse():
    return lambda r: str(r)


@pytest.fixture(scope="module")
def assert_equivalent_automata() -> Callable[[Automaton, Automaton], None]:
    def _assert_equivalent_automata(a: Automaton, b: Automaton) -> None:
        if not a.subsetOf(b):
            example = str(a.minus(b).getShortestExample(True))
            raise AssertionError(
                f"Automaton a is not subset of b; counterexample: {example!r}"
            )
        if not b.subsetOf(a):
            example = str(b.minus(a).getShortestExample(True))
            raise AssertionError(
                f"Automaton b is not subset of a; counterexample: {example!r}"
            )

    return _assert_equivalent_automata


@pytest.fixture
def create_automaton() -> Callable[[str], Automaton]:
    def _create_automaton(regex: str, holes: Mapping[str, Automaton] = {}) -> Automaton:
        parsed = parse_regex(regex)
        automaton = parsed.to_automaton(holes)
        automaton = automaton.intersection(ALPHABET_AUTOMATON)
        automaton.minimize()
        return automaton

    return _create_automaton
