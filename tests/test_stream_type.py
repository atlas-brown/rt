import string

import pytest
from hypothesis import given
from hypothesis import strategies as st

from rt.regular_types.stream_type import _preprocess_char_set


_SAFE_ALPHABET = string.ascii_letters + string.digits + " _.,+@#$%^&*=/?<>;:'\"`~"

_ESCAPE_DICT = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "v": "\v",
    "f": "\f",
    "b": "\b",
    "s": " ",
}


@given(st.text(alphabet=_SAFE_ALPHABET, max_size=30))
def test_flat_strings_pass_through_unchanged(input_str: str):
    assert _preprocess_char_set(input_str) == input_str


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("a-c", "abc"),
        ("a-z", string.ascii_lowercase),
        ("0-9", string.digits),
        ("A-F", "ABCDEF"),
    ],
)
def test_range_expansion(input_str: str, expected: str):
    assert _preprocess_char_set(input_str) == expected


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("-abc", "-abc"),
        ("-", "-"),
    ],
)
def test_dash_at_start_is_literal(input_str: str, expected: str):
    assert _preprocess_char_set(input_str) == expected


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("abc-", "abc-"),
    ],
)
def test_dash_at_end_is_literal(input_str: str, expected: str):
    assert _preprocess_char_set(input_str) == expected


@pytest.mark.parametrize("input_str", ["z-a", "9-0", "f-b"])
def test_invalid_range_raises_valueerror(input_str: str):
    with pytest.raises(ValueError, match="invalid range"):
        _preprocess_char_set(input_str)


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("[:lower:]", string.ascii_lowercase),
        ("[:upper:]", string.ascii_uppercase),
        ("[:digit:]", string.digits),
        ("[:alpha:]", string.ascii_lowercase + string.ascii_uppercase),
        (
            "[:alnum:]",
            string.ascii_lowercase + string.ascii_uppercase + string.digits,
        ),
        ("[:blank:]", " \t"),
        (
            "[:word:]",
            string.ascii_lowercase + string.ascii_uppercase + string.digits + "_",
        ),
        ("[:xdigit:]", string.digits + "abcdef" + "ABCDEF"),
        ("[:space:]", " \t\n\r\f\v"),
    ],
)
def test_posix_class_expansion(input_str: str, expected: str):
    assert _preprocess_char_set(input_str) == expected


@pytest.mark.parametrize(
    "input_str,expected",
    [
        (r"\n", "\n"),
        (r"\t", "\t"),
        (r"\\", "\\"),
        (r"\-", "-"),
        (r"\s", " "),
    ],
)
def test_representative_escape_sequences(input_str: str, expected: str):
    assert _preprocess_char_set(input_str) == expected


@given(st.sampled_from(sorted(_ESCAPE_DICT)))
def test_escape_sequences_resolve(c: str):
    assert _preprocess_char_set("\\" + c) == _ESCAPE_DICT[c]


def test_non_escaped_backslash_passes_through():
    assert _preprocess_char_set(r"\q") == "\\q"


def test_combination_range_and_escapes():
    result = _preprocess_char_set(r"a-c\n")
    assert result == "abc\n"


def test_empty_input():
    assert _preprocess_char_set("") == ""
