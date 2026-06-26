from collections.abc import Callable

import pytest

from stream.java_api import Automaton, RegExp
from stream.regex_parser import RegexParser, ast_to_automaton
from stream.regular_type import RegularType
from stream.signature_loader import SignatureLoader


@pytest.fixture(scope="module")
def assert_equivalent() -> Callable[[Automaton, Automaton], None]:
    def _assert_equivalent(a: Automaton, b: Automaton) -> None:
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

    return _assert_equivalent


@pytest.fixture(scope="module")
def minimized_automaton() -> Callable[[str], Automaton]:
    def _minimized_automaton(pattern: str) -> Automaton:
        automaton = RegularType(pattern).nfa.clone()
        automaton.setDeterministic(False)
        automaton.determinize()
        automaton.removeDeadTransitions()
        automaton.minimize()
        return automaton

    return _minimized_automaton


@pytest.fixture
def create_nfa() -> Callable[[str], Automaton]:
    def _create_nfa(regex: str) -> Automaton:
        parsed = RegexParser(regex).parse()
        nfa = ast_to_automaton(parsed)
        alphabet = RegExp(f"[{chr(0)}-{chr(255)}]*").toAutomaton()
        return nfa.intersection(alphabet)

    return _create_nfa


@pytest.fixture
def lookup_signature() -> Callable[[str], object]:
    def _lookup_signature(command_name: str):
        SignatureLoader.reset_instance()
        loader = SignatureLoader.get_instance("./src/stream/signatures")
        for signature in loader.signatures:
            if signature.command_name == command_name:
                return signature
        raise AssertionError(f"missing signature for {command_name}")

    return _lookup_signature


@pytest.fixture
def apply_signature():
    def _apply_signature(signature, input_type, invocation, env_annotations=None):
        if env_annotations is None:
            env_annotations = {}
        command_type = signature.determine_command_type(invocation, [], env_annotations)
        return signature.apply_command_type(command_type, input_type)

    return _apply_signature
