from hypothesis import given, settings
from hypothesis import strategies as st

from stream.java_api import Automaton, BasicAutomata
from stream.regular_type import RegularType


def get_result(expected_input: str, actual_input: str) -> bool:
    expected_type = RegularType(expected_input)
    actual_type = RegularType(actual_input)
    return actual_type.is_subtype(expected_type)[0]


def test_subtyping():
    assert get_result("[0-9]+", "[0-9]+") == True
    assert get_result("[0-9]+", "[0-9]") == True
    assert get_result("[0-9]", "[0-9]+") == False
    assert get_result("[0-9]*", "[0-9]+") == True
    assert get_result(".*", "[0-9]") == True
    assert get_result(".*", "[0-9]+") == True
    assert get_result(".+", "[0-9]+") == True
    assert get_result(".+", "[0-9]*") == False
    assert get_result("[0-9]+&[0-9a-z]+", "[0-9]+&[0-9a-z]") == True
    assert get_result("[0-9]+&[0-9a-z]+", "[0-9]*&[0-9a-z]*") == False
    assert get_result(".*", ".*Hello.*") == True
    assert get_result(".*", "(.*(MemTotal|MemFree).*)") == True
    assert (
        get_result(".*", r".*(\(https://raw.githubusercontent.com.*centos.*\)).*")
        == True
    )


# ---------------------------------------------------------------------------
# Hypothesis property-based tests
# ---------------------------------------------------------------------------

_SMALL_REGEX_STRATEGY = st.sampled_from(
    ["a", "b", "c", "a|b", "ab", "a*", "b+", "[a-z]+", "foo|bar", "([0-9]+)", "abc", ""]
)


@given(pattern=_SMALL_REGEX_STRATEGY)
def test_subtyping_reflexivity(pattern: str) -> None:
    rt = RegularType(pattern)
    assert rt.is_subtype(rt)[0]


@given(pattern=_SMALL_REGEX_STRATEGY)
def test_subtyping_empty_is_subtype_of_all(pattern: str) -> None:
    empty = RegularType(automaton=Automaton())
    rt = RegularType(pattern)
    assert empty.is_subtype(rt)[0]


@given(pattern=_SMALL_REGEX_STRATEGY)
def test_subtyping_all_are_subtype_of_top(pattern: str) -> None:
    rt = RegularType(pattern)
    top = RegularType(".*")
    assert rt.is_subtype(top)[0]


@given(left=_SMALL_REGEX_STRATEGY, right=_SMALL_REGEX_STRATEGY)
def test_subtyping_witness_correctness(left: str, right: str) -> None:
    left_rt = RegularType(left)
    right_rt = RegularType(right)
    result, witness = left_rt.is_subtype(right_rt, enable_witness=True)
    if not result:
        assert witness is not None
        left_accepts = not left_rt.nfa.intersection(
            BasicAutomata.makeString(witness)
        ).isEmpty()
        right_accepts = not right_rt.nfa.intersection(
            BasicAutomata.makeString(witness)
        ).isEmpty()
        assert left_accepts
        assert not right_accepts
