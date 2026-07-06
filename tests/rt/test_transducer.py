from hypothesis import given
from hypothesis import strategies as st

from rt.transducer import (
    compression_transducer,
    deletion_transducer,
    first_replacement_transducer,
    global_replacement_transducer,
    translation_transducer,
)

_SMALL_ALPHABET = "abc"
_REPLACEMENT_ALPHABET = "xy"


def _unique_chars(s: str) -> str:
    return "".join(dict.fromkeys(s))


# TODO: Add docstrings explaining what properties are being tested in each test


@given(
    from_chars=st.text(alphabet=_SMALL_ALPHABET, min_size=1, max_size=3).map(
        _unique_chars
    ),
    to_chars=st.text(alphabet=_REPLACEMENT_ALPHABET, min_size=1, max_size=3).map(
        _unique_chars
    ),
    text=st.text(alphabet=_SMALL_ALPHABET + _REPLACEMENT_ALPHABET, max_size=50),
)
def test_translation_transducer_property(from_chars: str, to_chars: str, text: str) -> None:
    fst = translation_transducer(from_chars, to_chars)
    expected = ""
    for char in text:
        if char in from_chars:
            index = from_chars.index(char)
            if index < len(to_chars):
                expected += to_chars[index]
            else:
                expected += to_chars[-1]
        else:
            expected += char
    assert fst.transform_all(text) == {expected}


@given(data=st.data())
def test_compression_transducer_property(data: st.DataObject) -> None:
    chars_to_compress = data.draw(
        st.text(alphabet=_SMALL_ALPHABET, min_size=1, max_size=3).map(_unique_chars),
        label="chars_to_compress",
    )
    text = data.draw(st.text(alphabet=chars_to_compress, max_size=50), label="text")
    fst = compression_transducer(chars_to_compress)
    result = next(iter(fst.transform_all(text)))
    for i in range(len(result) - 1):
        assert not (result[i] == result[i + 1])


@given(
    chars_to_delete=st.text(alphabet=_SMALL_ALPHABET, min_size=1, max_size=3).map(
        _unique_chars
    ),
    text=st.text(alphabet=_SMALL_ALPHABET + _REPLACEMENT_ALPHABET, max_size=50),
)
def test_deletion_transducer_property(chars_to_delete: str, text: str) -> None:
    fst = deletion_transducer(chars_to_delete)
    result = next(iter(fst.transform_all(text)))
    for c in chars_to_delete:
        assert c not in result


@given(
    pattern=st.text(alphabet=_SMALL_ALPHABET, min_size=1, max_size=3),
    replacement=st.text(alphabet=_REPLACEMENT_ALPHABET, max_size=3),
    text=st.text(alphabet=_SMALL_ALPHABET + _REPLACEMENT_ALPHABET, max_size=50),
)
def test_global_replacement_transducer_property(
    pattern: str, replacement: str, text: str
) -> None:
    fst = global_replacement_transducer(pattern, replacement)
    expected = text.replace(pattern, replacement)
    assert fst.transform_all(text) == {expected}


@given(
    pattern=st.text(alphabet=_SMALL_ALPHABET, min_size=1, max_size=3),
    replacement=st.text(alphabet=_REPLACEMENT_ALPHABET, max_size=3),
    text=st.text(alphabet=_SMALL_ALPHABET + _REPLACEMENT_ALPHABET, max_size=50),
)
def test_first_replacement_transducer_property(
    pattern: str, replacement: str, text: str
) -> None:
    fst = first_replacement_transducer(pattern, replacement)
    expected = text.replace(pattern, replacement, 1)
    assert fst.transform_all(text) == {expected}
