import string

from hypothesis import given
from hypothesis import strategies as st

from rt.transducer import (
    compression_transducer,
    correct_cut_field_transducer,
    create_transducer,
    deletion_transducer,
    first_replacement_transducer,
    global_replacement_transducer,
    product_transducer_automaton,
    start_regex_replacement_transducer,
    translation_transducer,
)

_SMALL_ALPHABET = string.ascii_lowercase[:12]
_REPLACEMENT_ALPHABET = string.ascii_lowercase[12:20]


def _unique_chars(s: str) -> str:
    return "".join(dict.fromkeys(s))


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
    """Tests that translation_transducer maps each from_char to the corresponding
    to_char and passes through characters not in from_chars."""
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
    """Tests that compression_transducer produces output with no consecutive
    duplicate characters among the compressed set."""
    chars_to_compress = data.draw(
        st.text(alphabet=_SMALL_ALPHABET, min_size=1, max_size=3).map(_unique_chars),
        label="chars_to_compress",
    )
    text = data.draw(
        st.text(
            alphabet=chars_to_compress + _REPLACEMENT_ALPHABET,
            max_size=50,
        ),
        label="text",
    )
    fst = compression_transducer(chars_to_compress)
    result = next(iter(fst.transform_all(text)))
    assert result or not text
    for i in range(len(result) - 1):
        if result[i] in chars_to_compress and result[i + 1] in chars_to_compress:
            assert result[i] != result[i + 1]


@given(
    chars_to_delete=st.text(alphabet=_SMALL_ALPHABET, min_size=1, max_size=3).map(
        _unique_chars
    ),
    text=st.text(alphabet=_SMALL_ALPHABET + _REPLACEMENT_ALPHABET, max_size=50),
)
def test_deletion_transducer_property(chars_to_delete: str, text: str) -> None:
    """Tests that deletion_transducer removes all occurrences of the specified
    characters from the input while preserving the order of remaining characters."""
    fst = deletion_transducer(chars_to_delete)
    result = next(iter(fst.transform_all(text)))
    expected = "".join(c for c in text if c not in chars_to_delete)
    assert result == expected


@given(
    pattern=st.text(alphabet=_SMALL_ALPHABET, min_size=1, max_size=3),
    replacement=st.text(alphabet=_REPLACEMENT_ALPHABET, max_size=3),
    text=st.text(alphabet=_SMALL_ALPHABET + _REPLACEMENT_ALPHABET, max_size=50),
)
def test_global_replacement_transducer_property(
    pattern: str, replacement: str, text: str
) -> None:
    """Tests that global_replacement_transducer replaces all occurrences of a
    pattern with a replacement string, matching str.replace semantics."""
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
    """Tests that first_replacement_transducer replaces only the first
    occurrence of a pattern with a replacement string."""
    fst = first_replacement_transducer(pattern, replacement)
    expected = text.replace(pattern, replacement, 1)
    assert fst.transform_all(text) == {expected}


def test_inverse_fst() -> None:
    """Tests that a translation transducer's inverse maps output characters
    back to their originals and rejects invalid sequences."""
    fst = translation_transducer("abc", "def")
    fst_inverse = fst.inverse()
    assert fst_inverse.transform_all("d") == {"a", "d"}
    assert fst_inverse.transform_all("adef") == set()


def test_string_output() -> None:
    """Tests that inverse() correctly handles transducers with multi-character
    string output labels on transitions."""
    fst = create_transducer(
        [
            (0, "$epsilon", "hello", 1),
            (1, "a", "world", 2),
        ],
        0,
        {2},
    )
    fst_inverse = fst.inverse()
    assert fst_inverse.transform_all("helloworld") == {"a"}


def test_range_input_output() -> None:
    """Tests that inverse() correctly handles range-based input/output and
    $self references."""
    fst = create_transducer(
        [
            (0, "a--z", "$self", 1),
            (1, "a--b", "x", 3),
        ],
        0,
        {3},
    )
    fst_inverse = fst.inverse()
    assert fst_inverse.transform_all("x") == set()
    assert fst_inverse.transform_all("ax") == {"aa", "ab"}


def test_range_input_string_output() -> None:
    """Tests that inverse() correctly handles range input combined with string
    output."""
    fst = create_transducer(
        [
            (0, "a--z", "$self", 1),
            (1, "a--b", "xyz", 3),
        ],
        0,
        {3},
    )
    fst_inverse = fst.inverse()
    assert fst_inverse.transform_all("xyz") == set()
    assert fst_inverse.transform_all("ax") == set()
    assert fst_inverse.transform_all("axyz") == {"aa", "ab"}


def test_epsilon_output(create_automaton, assert_equivalent_automata) -> None:
    """Tests that inverse() expands epsilon outputs (compression), producing a
    transducer that when composed with an NFA yields the uncompressed language."""
    fst = compression_transducer("a")
    fst_inverse = fst.inverse()
    nfa = create_automaton("a")
    expected = create_automaton("a+")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert_equivalent_automata(expected, actual)
    nfa = create_automaton("aa+")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert actual.isEmpty()
    nfa = create_automaton("bab")
    expected = create_automaton("ba+b")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert_equivalent_automata(expected, actual)


def test_cut_field_fst(create_automaton, assert_equivalent_automata) -> None:
    """Tests that inverse() of a cut field transducer correctly reverses the
    field extraction mapping."""
    fst = correct_cut_field_transducer(" ", [3])
    fst_inverse = fst.inverse()
    nfa = create_automaton("a* b* c* d*")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert actual.isEmpty()
    nfa = create_automaton("x")
    expected = create_automaton("x|[^ ]* [^ ]* x( .*)?")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert_equivalent_automata(expected, actual)
    nfa = create_automaton("a*b*c+")
    expected = create_automaton("a*b*c+|[^ ]* [^ ]* a*b*c+( .*)?")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert_equivalent_automata(expected, actual)


def test_start_regex_replacement_transducer(create_automaton, assert_equivalent_automata) -> None:
    """Tests that inverse() of a start-regex replacement transducer preserves
    the language relationship between matched prefixes and replacements."""
    fst = start_regex_replacement_transducer(create_automaton("a*b*"), "x")
    fst_inverse = fst.inverse()
    nfa = create_automaton("a{2}b+")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert actual.isEmpty()
    nfa = create_automaton("y")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert actual.isEmpty()
    nfa = create_automaton("x*")
    expected = create_automaton("a*b*x*")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert_equivalent_automata(expected, actual)

    fst = start_regex_replacement_transducer(create_automaton("a.*b"), "x")
    fst_inverse = fst.inverse()
    nfa = create_automaton("a*b*")
    expected = create_automaton("a*|b*")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert_equivalent_automata(expected, actual)
    nfa = create_automaton("x|a*b*")
    expected = create_automaton("a*b*|a.*b|x")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert_equivalent_automata(expected, actual)

    fst = start_regex_replacement_transducer(create_automaton("a.*b"), "xyz")
    fst_inverse = fst.inverse()
    nfa = create_automaton("a*b*")
    expected = create_automaton("a*|b*")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert_equivalent_automata(expected, actual)
    nfa = create_automaton("xyz|a*b*")
    expected = create_automaton("a*b*|a.*b|xyz")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert_equivalent_automata(expected, actual)


def test_string_replacement_fst(create_automaton, assert_equivalent_automata) -> None:
    """Tests that inverse() of a global string replacement transducer correctly
    handles overlapping patterns and boundary conditions."""
    fst = global_replacement_transducer("ababc", "xyxyz")
    fst_inverse = fst.inverse()
    nfa = create_automaton("abababababc")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert actual.isEmpty()
    nfa = create_automaton("xyxyxyz")
    expected = create_automaton("xy(ababc|xyxyz)")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert_equivalent_automata(expected, actual)
    nfa = create_automaton("xyxyxyxyxyxyxyxyz")
    expected = create_automaton("xyxyxyxyxyxy(ababc|xyxyz)")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert_equivalent_automata(expected, actual)
    nfa = create_automaton("abab(x*y*)*z*")
    expected = create_automaton("abab(x*y*)*z*|abab(x*y*)*ababcz*")
    actual = product_transducer_automaton(fst_inverse, nfa)
    assert_equivalent_automata(expected, actual)
