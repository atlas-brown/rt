from stream.transducer import (
    add_newline_if_not_end_with_newline_FST,
    correct_cut_field_FST,
    create_fst,
    cut_char_FST,
    line_based_functional_to_stream_FST,
    product_fst_automaton,
)


class TestCutCharFST:
    """Test suite for product FST automaton operations."""

    def test_cut_char_fst(self, create_nfa, assert_equivalent) -> None:
        """Test product FST automaton functionality."""
        cut_fst = cut_char_FST([1, 2, 3], has_upperbound=True)
        nfa1 = create_nfa("a*")
        expected = create_nfa("a{0,3}")
        actual = product_fst_automaton(cut_fst, nfa1)
        assert_equivalent(expected, actual)
        nfa2 = create_nfa("ab?c?d*")
        expected = create_nfa("a|ab|ac|abc|abd|acd|ad|add")
        actual = product_fst_automaton(cut_fst, nfa2)
        assert_equivalent(expected, actual)
        nfa3 = create_nfa("a(b?c)*d*")
        expected = create_nfa("a|ac|abc|ad|add|acd|acb|acc")
        actual = product_fst_automaton(cut_fst, nfa3)
        assert_equivalent(expected, actual)

    def test_cut_field_fst(self, create_nfa, assert_equivalent) -> None:
        """Test product FST automaton functionality."""
        cut_fst = correct_cut_field_FST(" ", [3])
        nfa1 = create_nfa(".*")
        expected = create_nfa("[^ ]*")
        actual = product_fst_automaton(cut_fst, nfa1)
        assert_equivalent(expected, actual)
        nfa2 = create_nfa("a* b* c* [^ ]*")
        expected = create_nfa("c*")
        actual = product_fst_automaton(cut_fst, nfa2)
        assert_equivalent(expected, actual)
        nfa3 = create_nfa("[0-9]+|a* b* c* d*")
        expected = create_nfa("c*|[0-9]+")
        actual = product_fst_automaton(cut_fst, nfa3)
        assert_equivalent(expected, actual)

    def test_cut_field_whole_stream(self, create_nfa, assert_equivalent) -> None:
        """Test product FST automaton functionality."""
        cut_fst = line_based_functional_to_stream_FST(correct_cut_field_FST(" ", [3]))
        nfa1 = create_nfa("([^\n]*\n)*")
        expected = create_nfa("([^\n ]*\n)*")
        actual = product_fst_automaton(cut_fst, nfa1)
        assert_equivalent(expected, actual)
        nfa2 = create_nfa("([^\n]*\n)*([^\n]\n?)?")
        expected = create_nfa("([^\n ]*\n)*([^\n ]\n?)?")
        actual = product_fst_automaton(cut_fst, nfa2)
        assert_equivalent(expected, actual)

    def test_ls_cut_field(self, create_nfa, assert_equivalent) -> None:
        cut_fst = line_based_functional_to_stream_FST(
            correct_cut_field_FST(" ", [3], has_upperbound=True)
        )
        nfa3 = create_nfa("total 80\n([drwx-]{10}( )+[0-9]+( )+[a-zA-Z]+( )+[^\n]*\n)*")
        expected = create_nfa("\n((()|[0-9]+|[a-zA-Z]+)\n)*")
        actual = product_fst_automaton(cut_fst, nfa3)
        assert_equivalent(expected, actual)

    def test_cut_char_whole_stream(self, create_nfa, assert_equivalent) -> None:
        cut_fst = line_based_functional_to_stream_FST(
            cut_char_FST([1, 2], has_upperbound=True)
        )
        nfa1 = create_nfa(
            "FLying so high,\nAMong modern net's\nINspired world-view:\nGOod as it gets!"
        )
        expected = create_nfa("FL\nAM\nIN\nGO")
        actual = product_fst_automaton(cut_fst, nfa1)
        assert_equivalent(expected, actual)

    def test_add_newline_if_not_end_with_newline_FST(
        self, create_nfa, assert_equivalent
    ) -> None:
        fst = add_newline_if_not_end_with_newline_FST()
        nfa1 = create_nfa("(a*\n)+b+")
        expected = create_nfa("(a*\n)+b+\n")
        actual = product_fst_automaton(fst, nfa1)
        assert_equivalent(expected, actual)

        nfa1 = create_nfa("(a*\n)+b+\n")
        expected = create_nfa("(a*\n)+b+\n")
        actual = product_fst_automaton(fst, nfa1)
        assert_equivalent(expected, actual)


class TestEpsilonTransitions:
    def test_epsilon_transitions(self, create_nfa, assert_equivalent) -> None:
        fst = create_fst(
            [
                (0, "$epsilon", "hello", 1),
                (1, "a", "world", 2),
            ],
            0,
            {2},
        )
        nfa1 = create_nfa("a*")
        expected = create_nfa("helloworld")
        actual = product_fst_automaton(fst, nfa1)
        assert_equivalent(expected, actual)

        fst = create_fst(
            [
                (0, "$epsilon", "hello", 0),
                (0, "a", "world", 1),
            ],
            0,
            {1},
        )
        nfa1 = create_nfa("a")
        expected = create_nfa("(hello)*world")
        actual = product_fst_automaton(fst, nfa1)
        assert_equivalent(expected, actual)
        nfa2 = create_nfa("a*")
        expected = create_nfa("(hello)*world")
        actual = product_fst_automaton(fst, nfa2)
        assert_equivalent(expected, actual)
        nfa3 = create_nfa("a*b+")
        actual = product_fst_automaton(fst, nfa3)
        assert actual.isEmpty()

        fst = create_fst(
            [
                (0, "$epsilon", "x", 1),
                (1, "$epsilon", "y", 1),
                (1, "a", "z", 1),
            ],
            0,
            {1},
        )
        nfa1 = create_nfa("a*")
        expected = create_nfa("x(y|z)*")
        actual = product_fst_automaton(fst, nfa1)
        assert_equivalent(expected, actual)
