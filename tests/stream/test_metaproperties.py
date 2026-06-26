from hypothesis import given, settings
from hypothesis import strategies as st

from stream.regular_type import RegularType
from stream.transducer import (
    compression_FST,
    deletion_FST,
    product_fst_automaton,
    translation_FST,
)

simple_regex_strategy = st.sampled_from(
    [
        ".+",
        "[a-z]+",
        "foo|bar",
        "a*b",
        "([0-9]+)",
        "a",
        "b",
        "c",
        "a|b",
        "ab",
        "a*",
        "b+",
        "[abc]",
        "[^abc]",
        "abc",
        "",
        "a{3,5}",
        "(a|b)c",
        "[a-zA-Z0-9]+",
        "ab|cd",
    ]
)


@given(
    a=simple_regex_strategy,
    b=simple_regex_strategy,
    c=simple_regex_strategy,
)
def test_subtyping_transitivity(a: str, b: str, c: str) -> None:
    A = RegularType(a)
    B = RegularType(b)
    C = RegularType(c)
    if A.is_subtype(B)[0] and B.is_subtype(C)[0]:
        assert A.is_subtype(C)[0]


@given(a=simple_regex_strategy, b=simple_regex_strategy)
def test_union_commutativity(a: str, b: str, assert_equivalent) -> None:
    A = RegularType(a)
    B = RegularType(b)
    assert_equivalent((A | B).nfa, (B | A).nfa)


@given(a=simple_regex_strategy, b=simple_regex_strategy, c=simple_regex_strategy)
def test_union_associativity(a: str, b: str, c: str, assert_equivalent) -> None:
    A = RegularType(a)
    B = RegularType(b)
    C = RegularType(c)
    assert_equivalent(((A | B) | C).nfa, (A | (B | C)).nfa)


@given(a=simple_regex_strategy, b=simple_regex_strategy)
def test_intersection_commutativity(a: str, b: str, assert_equivalent) -> None:
    A = RegularType(a)
    B = RegularType(b)
    assert_equivalent((A & B).nfa, (B & A).nfa)


@given(a=simple_regex_strategy, b=simple_regex_strategy, c=simple_regex_strategy)
def test_intersection_associativity(a: str, b: str, c: str, assert_equivalent) -> None:
    A = RegularType(a)
    B = RegularType(b)
    C = RegularType(c)
    assert_equivalent(((A & B) & C).nfa, (A & (B & C)).nfa)


@given(a=simple_regex_strategy)
def test_double_complement(a: str, assert_equivalent) -> None:
    A = RegularType(a)
    assert_equivalent((~~A).nfa, A.nfa)


@given(a=simple_regex_strategy, b=simple_regex_strategy)
def test_de_morgan_union(a: str, b: str, assert_equivalent) -> None:
    A = RegularType(a)
    B = RegularType(b)
    assert_equivalent((~(A | B)).nfa, (~A & ~B).nfa)


@given(a=simple_regex_strategy, b=simple_regex_strategy)
def test_de_morgan_intersection(a: str, b: str, assert_equivalent) -> None:
    A = RegularType(a)
    B = RegularType(b)
    assert_equivalent((~(A & B)).nfa, (~A | ~B).nfa)


@given(a=simple_regex_strategy, b=simple_regex_strategy, c=simple_regex_strategy)
def test_concatenation_associativity(a: str, b: str, c: str, assert_equivalent) -> None:
    A = RegularType(a)
    B = RegularType(b)
    C = RegularType(c)
    assert_equivalent(((A + B) + C).nfa, (A + (B + C)).nfa)


@given(
    chars=st.text(alphabet="abc", min_size=1, max_size=3).map(
        lambda s: "".join(dict.fromkeys(s))
    ),
    text=st.text(alphabet="abc", max_size=50),
)
def test_compression_idempotence(chars: str, text: str) -> None:
    fst = compression_FST(chars)
    once = next(iter(fst.transform_all(text)))
    twice = next(iter(fst.transform_all(once)))
    assert once == twice


@given(
    a=simple_regex_strategy,
    b=simple_regex_strategy,
    chars=st.text(alphabet="abc", min_size=1, max_size=3).map(
        lambda s: "".join(dict.fromkeys(s))
    ),
)
def test_product_monotonicity_translation(a: str, b: str, chars: str) -> None:
    A = RegularType(a)
    B = RegularType(b)
    if A.is_subtype(B)[0]:
        fst = translation_FST(chars, "xyz"[: len(chars)])
        pa = product_fst_automaton(fst, A.nfa)
        pb = product_fst_automaton(fst, B.nfa)
        assert pa.subsetOf(pb)


@given(
    a=simple_regex_strategy,
    b=simple_regex_strategy,
    chars=st.text(alphabet="abc", min_size=1, max_size=3).map(
        lambda s: "".join(dict.fromkeys(s))
    ),
)
def test_product_monotonicity_deletion(a: str, b: str, chars: str) -> None:
    A = RegularType(a)
    B = RegularType(b)
    if A.is_subtype(B)[0]:
        fst = deletion_FST(chars)
        pa = product_fst_automaton(fst, A.nfa)
        pb = product_fst_automaton(fst, B.nfa)
        assert pa.subsetOf(pb)
