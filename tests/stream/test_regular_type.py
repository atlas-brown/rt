from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from stream.java_api import BasicAutomata, BasicOperations
from stream.regular_type import RegularType, preprocess

_SMALL_PATTERNS = [
    "a",
    "b",
    "ab",
    "abc",
    "a|b",
    "ab|cd",
    "a*",
    "b+",
    "a?",
    "[a-z]+",
    "[abc]",
    "[^abc]",
    "foo|bar",
    "([0-9]+)",
    "",
    "a{3,5}",
    "(a|b)c",
]


def test_empty_intersection_disjoint() -> None:
    a = RegularType("abc")
    b = RegularType("def")
    assert a.empty_intersection(b)


def test_empty_intersection_overlapping() -> None:
    a = RegularType("a.*")
    b = RegularType(".*b")
    assert not a.empty_intersection(b)


@given(st.sampled_from(_SMALL_PATTERNS))
def test_empty_intersection_self_is_not_disjoint(pattern: str) -> None:
    rt = RegularType(pattern)
    assert not rt.empty_intersection(rt)


def test_not_subtype_inverse() -> None:
    a = RegularType("abc")
    b = RegularType(".*")
    assert a.is_subtype(b)[0]
    assert not a.not_subtype(b)[0]

    c = RegularType("a+")
    d = RegularType("b+")
    assert c.not_subtype(d)[0]
    assert not c.is_subtype(d)[0]


@given(st.sampled_from(_SMALL_PATTERNS))
def test_not_subtype_is_logical_inverse(pattern: str) -> None:
    rt = RegularType(pattern)
    top = RegularType(".*")
    result, witness = rt.is_subtype(top)
    not_result, not_witness = rt.not_subtype(top)
    assert result != not_result
    assert witness == not_witness


def test_get_shortest_example_accepted() -> None:
    rt = RegularType("a*b")
    example = rt.get_shortest_example()
    assert rt.nfa.run(example)


def test_get_shortest_example_empty_string() -> None:
    rt = RegularType("")
    assert rt.get_shortest_example() == ""


@given(st.sampled_from([p for p in _SMALL_PATTERNS if p != ""]))
def test_get_shortest_example_is_accepted(pattern: str) -> None:
    rt = RegularType(pattern)
    example = rt.get_shortest_example()
    assert rt.nfa.run(example)


def test_is_empty_true() -> None:
    rt = RegularType("a&~a")
    assert rt.is_empty()

    rt2 = RegularType(automaton=BasicAutomata.makeEmpty())
    assert rt2.is_empty()


def test_is_empty_false() -> None:
    rt = RegularType("abc")
    assert not rt.is_empty()

    rt2 = RegularType("")
    assert not rt2.is_empty()


def test_is_empty_string_true() -> None:
    rt = RegularType("")
    assert rt.is_empty_string()

    rt2 = RegularType(automaton=BasicAutomata.makeEmptyString())
    assert rt2.is_empty_string()


def test_is_empty_string_false() -> None:
    rt = RegularType("abc")
    assert not rt.is_empty_string()

    rt2 = RegularType("a+")
    assert not rt2.is_empty_string()


def test_to_regex_round_trip_explicit(assert_equivalent) -> None:
    for pattern in ["abc", "a+", "a*", "foo|bar", "[a-z]+", "", "a{3,5}"]:
        rt = RegularType(pattern)
        regex = rt.to_regex()
        if regex.startswith("initial state:"):
            pytest.skip("to_regex returned raw automaton fallback")
        rt2 = RegularType(regex)
        assert_equivalent(rt.nfa, rt2.nfa)


@given(pattern=st.sampled_from(_SMALL_PATTERNS))
def test_to_regex_produces_equivalent_automaton(
    pattern: str, assert_equivalent
) -> None:
    rt = RegularType(pattern)
    regex = rt.to_regex()
    if regex.startswith("initial state:"):
        pytest.skip("to_regex returned raw automaton fallback")
    rt2 = RegularType(regex)
    assert_equivalent(rt.nfa, rt2.nfa)


def test_get_singleton_singleton() -> None:
    rt = RegularType("abc")
    assert rt.get_singleton() == "abc"

    rt2 = RegularType("a")
    assert rt2.get_singleton() == "a"

    rt3 = RegularType(r"\.")
    assert rt3.get_singleton() == r"\."


def test_get_singleton_non_singleton() -> None:
    rt = RegularType("a+")
    assert rt.get_singleton() is None

    rt2 = RegularType("a|b")
    assert rt2.get_singleton() is None

    rt3 = RegularType("a*")
    assert rt3.get_singleton() is None


def test_get_singleton_empty_string() -> None:
    rt = RegularType("")
    assert rt.get_singleton() == ""


def test_operator_add(assert_equivalent) -> None:
    a = RegularType("abc")
    b = RegularType("def")
    result = a + b
    expected = RegularType(automaton=BasicOperations.concatenate(a.nfa, b.nfa))
    assert_equivalent(result.nfa, expected.nfa)


def test_operator_sub(assert_equivalent) -> None:
    a = RegularType("abc|def")
    b = RegularType("abc")
    result = a - b
    expected = RegularType(automaton=BasicOperations.minus(a.nfa, b.nfa))
    assert_equivalent(result.nfa, expected.nfa)


def test_operator_and(assert_equivalent) -> None:
    a = RegularType("abc|abd")
    b = RegularType("ab.")
    result = a & b
    expected = RegularType(automaton=BasicOperations.intersection(a.nfa, b.nfa))
    assert_equivalent(result.nfa, expected.nfa)


def test_operator_or(assert_equivalent) -> None:
    a = RegularType("abc")
    b = RegularType("def")
    result = a | b
    expected = RegularType(automaton=BasicOperations.union(a.nfa, b.nfa))
    assert_equivalent(result.nfa, expected.nfa)


def test_operator_invert() -> None:
    a = RegularType("abc")
    not_a = ~a
    # a and ~a should be disjoint
    assert (a & not_a).is_empty()


def test_operator_optional(assert_equivalent) -> None:
    a = RegularType("abc")
    result = a.optional()
    expected = RegularType(automaton=BasicOperations.optional(a.nfa))
    assert_equivalent(result.nfa, expected.nfa)


def test_operator_kleene_star(assert_equivalent) -> None:
    a = RegularType("abc")
    result = a.kleene_star()
    expected = RegularType(automaton=BasicOperations.repeat(a.nfa, 0))
    assert_equivalent(result.nfa, expected.nfa)


def test_operator_kleene_plus(assert_equivalent) -> None:
    a = RegularType("abc")
    result = a.kleene_plus()
    expected = RegularType(automaton=BasicOperations.repeat(a.nfa, 1))
    assert_equivalent(result.nfa, expected.nfa)


def test_operator_reverse(assert_equivalent) -> None:
    a = RegularType("abc")
    result = a.reverse()
    # reverse is an involution for this pattern
    assert_equivalent(result.reverse().nfa, a.nfa)


@given(left=st.sampled_from(_SMALL_PATTERNS), right=st.sampled_from(_SMALL_PATTERNS))
def test_operators_are_equivalent_to_brics(
    left: str, right: str, assert_equivalent
) -> None:
    a = RegularType(left)
    b = RegularType(right)
    assert_equivalent((a + b).nfa, BasicOperations.concatenate(a.nfa, b.nfa))
    assert_equivalent((a | b).nfa, BasicOperations.union(a.nfa, b.nfa))
    assert_equivalent((a & b).nfa, BasicOperations.intersection(a.nfa, b.nfa))
    assert_equivalent((a - b).nfa, BasicOperations.minus(a.nfa, b.nfa))
    # complement: a & ~a should be empty
    assert (a & ~a).is_empty()
    assert_equivalent(a.optional().nfa, BasicOperations.optional(a.nfa))
    assert_equivalent(a.kleene_star().nfa, BasicOperations.repeat(a.nfa, 0))
    assert_equivalent(a.kleene_plus().nfa, BasicOperations.repeat(a.nfa, 1))
    # reverse is an involution
    assert_equivalent(a.reverse().reverse().nfa, a.nfa)


def test_preprocess_dollar_brace() -> None:
    assert preprocess("${VAR}") == "(.*)"
    assert preprocess("prefix${FOO}suffix") == "prefix(.*)suffix"


def test_preprocess_dollar_paren() -> None:
    assert preprocess("$(CMD)") == "(.*)"
    assert preprocess("$(echo hello)") == "(.*)"


def test_preprocess_escaped_dollar() -> None:
    assert preprocess(r"\$\{VAR\}") == "(.*)"
    assert preprocess(r"\$\(CMD\)") == "(.*)"


def test_preprocess_neg_lookahead() -> None:
    assert preprocess("(?!abc)") == "~(abc)"


def test_preprocess_mixed() -> None:
    assert preprocess("foo${VAR}bar$(CMD)baz(?!qux)") == "foo(.*)bar(.*)baz~(qux)"
