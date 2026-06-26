from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from stream.regex_parser import (
    RegexParser,
    ast_to_automaton,
    ast_to_regex,
    convert_to_pure_string,
    is_pure_string,
)

_PATTERNS = [
    "a",
    "ab",
    "a|b",
    "a*",
    "a+",
    "a?",
    "[abc]",
    "[^abc]",
    "[a-z]",
    "[[:digit:]]",
    "[[:alpha:]]",
    "[[:alnum:]]",
    "[[:lower:]]",
    "[[:upper:]]",
    "a{3,5}",
    "(a|b)c",
    "",
    "a&b",
    "~a",
    ".+",
    "[a-zA-Z0-9]+",
]


def test_compat_extended_equivalent_union(assert_equivalent) -> None:
    compat = ast_to_automaton(RegexParser("a|b", "compat").parse())
    extended = ast_to_automaton(RegexParser("a|b", "extended").parse())
    assert_equivalent(compat, extended)


def test_basic_equivalent_union(assert_equivalent) -> None:
    basic = ast_to_automaton(RegexParser(r"a\|b", "basic").parse())
    compat = ast_to_automaton(RegexParser("a|b", "compat").parse())
    assert_equivalent(basic, compat)


def test_basic_equivalent_quantifiers(assert_equivalent) -> None:
    for pattern, basic_pat in [
        ("a+", r"a\+"),
        ("a?", r"a\?"),
        ("a{3,5}", r"a\{3,5\}"),
    ]:
        basic = ast_to_automaton(RegexParser(basic_pat, "basic").parse())
        compat = ast_to_automaton(RegexParser(pattern, "compat").parse())
        assert_equivalent(basic, compat)


def test_basic_equivalent_group(assert_equivalent) -> None:
    basic = ast_to_automaton(RegexParser(r"\(a\|b\)", "basic").parse())
    compat = ast_to_automaton(RegexParser("(a|b)", "compat").parse())
    assert_equivalent(basic, compat)


def test_character_class_positive() -> None:
    ast = RegexParser("[abc]").parse()
    nfa = ast_to_automaton(ast)
    assert nfa.run("a")
    assert nfa.run("b")
    assert nfa.run("c")
    assert not nfa.run("d")


def test_character_class_negative() -> None:
    ast = RegexParser("[^abc]").parse()
    nfa = ast_to_automaton(ast)
    assert not nfa.run("a")
    assert not nfa.run("b")
    assert not nfa.run("c")
    assert nfa.run("d")


def test_character_class_range() -> None:
    ast = RegexParser("[a-z]").parse()
    nfa = ast_to_automaton(ast)
    assert nfa.run("a")
    assert nfa.run("m")
    assert nfa.run("z")
    assert not nfa.run("A")


def test_character_class_escaped_dash() -> None:
    ast = RegexParser(r"[a\-z]").parse()
    nfa = ast_to_automaton(ast)
    assert nfa.run("-")
    assert nfa.run("a")
    assert nfa.run("z")
    assert not nfa.run("b")


def test_character_class_escaped_bracket() -> None:
    ast = RegexParser(r"[a\]b]").parse()
    nfa = ast_to_automaton(ast)
    assert nfa.run("]")
    assert nfa.run("a")
    assert nfa.run("b")
    assert not nfa.run("c")


def test_posix_classes_accept_non_empty() -> None:
    classes = [
        "digit",
        "alpha",
        "alnum",
        "lower",
        "upper",
        "space",
        "punct",
        "xdigit",
        "blank",
        "cntrl",
        "graph",
        "print",
    ]
    for name in classes:
        ast = RegexParser(f"[[:{name}:]]").parse()
        nfa = ast_to_automaton(ast)
        assert not nfa.run("")


def test_posix_digit() -> None:
    ast = RegexParser("[[:digit:]]").parse()
    nfa = ast_to_automaton(ast)
    assert nfa.run("5")
    assert not nfa.run("a")


def test_posix_alpha() -> None:
    ast = RegexParser("[[:alpha:]]").parse()
    nfa = ast_to_automaton(ast)
    assert nfa.run("a")
    assert nfa.run("Z")
    assert not nfa.run("5")


def test_posix_alnum() -> None:
    ast = RegexParser("[[:alnum:]]").parse()
    nfa = ast_to_automaton(ast)
    assert nfa.run("a")
    assert nfa.run("5")
    assert not nfa.run(" ")


def test_hole_syntax() -> None:
    ast = RegexParser("{{name}}", "compat").parse()
    regex = ast_to_regex(ast)
    assert regex == "{{name}}"


def test_hole_in_expression() -> None:
    ast = RegexParser("a{{hole}}b", "compat").parse()
    regex = ast_to_regex(ast)
    assert regex == "a{{hole}}b"


def test_error_unterminated_class() -> None:
    with pytest.raises(ValueError, match="Unterminated character class"):
        RegexParser("[abc").parse()


def test_error_invalid_quantifier() -> None:
    with pytest.raises(ValueError, match="Missing number in quantifier"):
        RegexParser("a{").parse()


def test_error_unknown_posix_class() -> None:
    with pytest.raises(ValueError, match="Unknown POSIX character class"):
        RegexParser("[[:unknown:]]").parse()


def test_round_trip_explicit(assert_equivalent) -> None:
    for pattern in [
        "a",
        "ab",
        "a|b",
        "a*",
        "a+",
        "[abc]",
        "[^abc]",
        "[a-z]",
        "a{3,5}",
        "(a|b)c",
    ]:
        ast = RegexParser(pattern, "compat").parse()
        regex = ast_to_regex(ast)
        ast2 = RegexParser(regex, "compat").parse()
        nfa1 = ast_to_automaton(ast)
        nfa2 = ast_to_automaton(ast2)
        assert_equivalent(nfa1, nfa2)


@given(pattern=st.sampled_from(_PATTERNS))
def test_round_trip_hypothesis(pattern: str, assert_equivalent) -> None:
    ast = RegexParser(pattern, "compat").parse()
    regex = ast_to_regex(ast)
    ast2 = RegexParser(regex, "compat").parse()
    nfa1 = ast_to_automaton(ast)
    nfa2 = ast_to_automaton(ast2)
    assert_equivalent(nfa1, nfa2)


def test_is_pure_string_literal() -> None:
    assert is_pure_string("abc")
    assert is_pure_string("a")
    assert is_pure_string("[a]")


def test_is_pure_string_not_pure() -> None:
    assert not is_pure_string(".+")
    assert not is_pure_string("a*")
    assert not is_pure_string("a|b")
    assert not is_pure_string("[^a]")
    assert not is_pure_string("[ab]")


def test_convert_to_pure_string_literal() -> None:
    assert convert_to_pure_string("abc") == "abc"
    assert convert_to_pure_string("a") == "a"
    assert convert_to_pure_string("[a]") == "a"


def test_convert_to_pure_string_non_literal() -> None:
    assert convert_to_pure_string(".+") is None
    assert convert_to_pure_string("a*") is None
    assert convert_to_pure_string("a|b") is None
    assert convert_to_pure_string("[^a]") is None


def test_basic_mode_nested_group(assert_equivalent) -> None:
    """Test that basic mode escaped groups can be nested."""
    basic = ast_to_automaton(RegexParser(r"a\(b\(c\|d\)e\)f", "basic").parse())
    compat = ast_to_automaton(RegexParser("a(b(c|d)e)f", "compat").parse())
    assert_equivalent(basic, compat)
