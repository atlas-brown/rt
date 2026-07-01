from stream.transducer import (
    compression_FST,
    correct_cut_field_FST,
    create_fst,
    global_replacement_FST,
    product_fst_automaton,
    start_regex_replacement_FST,
    translation_FST,
)


class TestInverseFST:
    def test_inverse_fst(self) -> None:
        fst = translation_FST("abc", "def")
        fst_inverse = fst.inverse()
        assert fst_inverse.transform_all("d") == {"a", "d"}
        assert fst_inverse.transform_all("adef") == set()

    def test_string_output(self) -> None:
        fst = create_fst(
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
        fst = create_fst(
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
        fst = create_fst(
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

    def test_epsilon_output(self, create_nfa, assert_equivalent) -> None:
        fst = compression_FST("a")
        fst_inverse = fst.inverse()
        nfa = create_nfa("a")
        expected = create_nfa("a+")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equivalent(expected, actual)
        nfa = create_nfa("aa+")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert actual.isEmpty()
        nfa = create_nfa("bab")
        expected = create_nfa("ba+b")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equivalent(expected, actual)

    def test_cut_field_fst(self, create_nfa, assert_equivalent) -> None:
        fst = correct_cut_field_FST(" ", [3])
        fst_inverse = fst.inverse()
        nfa = create_nfa("a* b* c* d*")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert actual.isEmpty()
        nfa = create_nfa("x")
        expected = create_nfa("x|[^ ]* [^ ]* x( .*)?")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equivalent(expected, actual)
        nfa = create_nfa("a*b*c+")
        expected = create_nfa("a*b*c+|[^ ]* [^ ]* a*b*c+( .*)?")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equivalent(expected, actual)

    def test_start_regex_replacement_FST(self, create_nfa, assert_equivalent) -> None:
        fst = start_regex_replacement_FST(create_nfa("a*b*"), "x")
        fst_inverse = fst.inverse()
        nfa = create_nfa("a{2}b+")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert actual.isEmpty()
        nfa = create_nfa("y")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert actual.isEmpty()
        nfa = create_nfa("x*")
        expected = create_nfa("a*b*x*")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equivalent(expected, actual)

        fst = start_regex_replacement_FST(create_nfa("a.*b"), "x")
        fst_inverse = fst.inverse()
        nfa = create_nfa("a*b*")
        expected = create_nfa("a*|b*")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equivalent(expected, actual)
        nfa = create_nfa("x|a*b*")
        expected = create_nfa("a*b*|a.*b|x")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equivalent(expected, actual)

        fst = start_regex_replacement_FST(create_nfa("a.*b"), "xyz")
        fst_inverse = fst.inverse()
        nfa = create_nfa("a*b*")
        expected = create_nfa("a*|b*")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equivalent(expected, actual)
        nfa = create_nfa("xyz|a*b*")
        expected = create_nfa("a*b*|a.*b|xyz")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equivalent(expected, actual)

    def test_string_replacement_fst(self, create_nfa, assert_equivalent) -> None:
        fst = global_replacement_FST("ababc", "xyxyz")
        fst_inverse = fst.inverse()
        nfa = create_nfa("abababababc")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert actual.isEmpty()
        nfa = create_nfa("xyxyxyz")
        expected = create_nfa("xy(ababc|xyxyz)")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equivalent(expected, actual)
        nfa = create_nfa("xyxyxyxyxyxyxyxyz")
        expected = create_nfa("xyxyxyxyxyxy(ababc|xyxyz)")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equivalent(expected, actual)
        nfa = create_nfa("abab(x*y*)*z*")
        expected = create_nfa("abab(x*y*)*z*|abab(x*y*)*ababcz*")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equivalent(expected, actual)
