import jpype
import pytest
from stream.regex_parser import RegexParser, ast_to_automaton
from stream.transducer import correct_cut_field_FST, cut_char_FST, line_based_functional_to_stream_FST, product_fst_automaton, product_fst_automaton_with_projection
if not jpype.isJVMStarted():
    jpype.startJVM(classpath=["jars/automaton.jar"])
from dk.brics.automaton import RegExp, Automaton, BasicOperations, BasicAutomata, SpecialOperations, State, Transition # type: ignore

product_fst_automaton = product_fst_automaton_with_projection

def assert_equal(a: Automaton, b: Automaton) -> None:
    assert a.subsetOf(b)
    assert b.subsetOf(a)

def diff(a: Automaton, b: Automaton) -> str:
    diff_nfa = a.minus(b)
    s = str(diff_nfa.getShortestExample(True))
    # for c in s:
    #     print(ord(c))
    s = s.replace("\n", "\\n")
    return s

def create_nfa(regex: str) -> Automaton:
    return ast_to_automaton(RegexParser(regex).parse())

class TestCutCharFST:
    """Test suite for product FST automaton operations."""
    
    def test_cut_char_fst(self) -> None:
        """Test product FST automaton functionality."""
        cut_fst = cut_char_FST([1, 2, 3], has_upperbound=True)
        nfa1 = create_nfa("a*")
        expected = create_nfa("a{0,3}")
        actual = product_fst_automaton(cut_fst, nfa1)
        assert_equal(expected, actual)
        nfa2 = create_nfa("ab?c?d*")
        expected = create_nfa("a|ab|ac|abc|abd|acd|ad|add")
        actual = product_fst_automaton(cut_fst, nfa2)
        assert_equal(expected, actual)
        nfa3 = create_nfa("a(b?c)*d*")
        expected = create_nfa("a|ac|abc|ad|add|acd|acb|acc")
        actual = product_fst_automaton(cut_fst, nfa3)
        assert_equal(expected, actual)

    def test_cut_field_fst(self) -> None:
        """Test product FST automaton functionality."""
        cut_fst = correct_cut_field_FST(" ", [3])
        nfa1 = create_nfa(".*")
        expected = create_nfa("[^ ]*")
        actual = product_fst_automaton(cut_fst, nfa1)
        assert_equal(expected, actual)
        nfa2 = create_nfa("a* b* c* [^ ]*")
        expected = create_nfa("c*")
        actual = product_fst_automaton(cut_fst, nfa2)
        assert_equal(expected, actual)
        nfa3 = create_nfa("[0-9]+|a* b* c* d*")
        expected = create_nfa("c*|[0-9]+")
        actual = product_fst_automaton(cut_fst, nfa3)
        assert_equal(expected, actual)

    def test_cut_field_whole_stream(self) -> None:
        """Test product FST automaton functionality."""
        cut_fst = line_based_functional_to_stream_FST(correct_cut_field_FST(" ", [3]))
        nfa1 = create_nfa("([^\n]*\n)*")
        expected = create_nfa("([^\n ]*\n)*")
        actual = product_fst_automaton(cut_fst, nfa1)
        assert_equal(expected, actual)
        nfa2 = create_nfa("([^\n]*\n)*([^\n]\n?)?")
        expected = create_nfa("([^\n ]*\n)*([^\n ]\n?)?")
        actual = product_fst_automaton(cut_fst, nfa2)
        assert_equal(expected, actual)
    def test_ls_cut_field(self) -> None:
        cut_fst = line_based_functional_to_stream_FST(correct_cut_field_FST(" ", [3], has_upperbound=True))
        nfa3 = create_nfa("total 80\n([drwx-]{10}( )+[0-9]+( )+[a-zA-Z]+( )+[^\n]*\n)*")
        expected = create_nfa("\n((()|[0-9]+|[a-zA-Z]+)\n)*")
        actual = product_fst_automaton(cut_fst, nfa3)
        assert_equal(expected, actual)

    def test_cut_char_whole_stream(self) -> None:
        cut_fst = line_based_functional_to_stream_FST(cut_char_FST([1, 2], has_upperbound=True))
        nfa1 = create_nfa("FLying so high,\nAMong modern net's\nINspired world-view:\nGOod as it gets!")
        expected = create_nfa("FL\nAM\nIN\nGO")
        actual = product_fst_automaton(cut_fst, nfa1)
        assert_equal(expected, actual)



if __name__ == "__main__":
    pytest.main([__file__])
    jpype.shutdownJVM()