from rt.transducer import (
    compression_transducer,
    correct_cut_field_transducer,
    create_transducer,
    global_replacement_transducer,
    product_transducer_automaton,
    start_regex_replacement_transducer,
    translation_transducer,
)

# TODO: Add docstrings explaining what properties are being tested in each test
# TODO: Merge with tests/rt/test_transducer.py


# TODO: Turn the class structure into just functions, unless there is good reason to not do so
class TestInverseFST:
    def test_inverse_fst(self) -> None:
        fst = translation_transducer("abc", "def")
        fst_inverse = fst.inverse()
        assert fst_inverse.transform_all("d") == {"a", "d"}
        assert fst_inverse.transform_all("adef") == set()

    def test_string_output(self) -> None:
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

    def test_range_input_output(self) -> None:
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

    def test_range_input_string_output(self) -> None:
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

    def test_epsilon_output(self, create_automaton, assert_equivalent_automata) -> None:
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

    def test_cut_field_fst(self, create_automaton, assert_equivalent_automata) -> None:
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

    def test_start_regex_replacement_transducer(self, create_automaton, assert_equivalent_automata) -> None:
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

    def test_string_replacement_fst(self, create_automaton, assert_equivalent_automata) -> None:
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
