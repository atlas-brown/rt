import traceback
import jpype
import pytest
from stream.regex_parser import RegexParser, ast_to_automaton
from stream.transducer import compression_FST, correct_cut_field_FST, create_fst, cut_char_FST, global_replacement_FST, line_based_functional_to_stream_FST, product_fst_automaton, product_fst_automaton_with_projection, start_regex_replacement_FST, translation_FST
if not jpype.isJVMStarted():
    jpype.startJVM(classpath=["jars/automaton.jar"])
from dk.brics.automaton import RegExp, Automaton, BasicOperations, BasicAutomata, SpecialOperations, State, Transition # type: ignore

alphabet_size = 255
alphabet_automaton = RegExp(f"[{chr(0)}-{chr(alphabet_size)}]*").toAutomaton()

def create_nfa(regex: str) -> Automaton:
    return ast_to_automaton(RegexParser(regex).parse()).intersection(alphabet_automaton)

def assert_equal(a: Automaton, b: Automaton) -> None:
    assert a.subsetOf(b)
    assert b.subsetOf(a)

def diff(a: Automaton, b: Automaton) -> str:
    diff_nfa = a.minus(b)
    s = str(diff_nfa.getShortestExample(True))
    for c in s:
        print(ord(c))
    s = s.replace("\n", "\\n")
    return s

# product_fst_automaton = product_fst_automaton_with_projection

class TestInverseFST:
    def test_inverse_fst(self) -> None:
        fst = translation_FST("abc", "def")
        fst_inverse = fst.inverse()
        assert fst_inverse.transform_all("d") == {"a", "d"}
        assert fst_inverse.transform_all("adef") == set()
    
    def test_string_output(self) -> None:
        fst = create_fst([
            (0, "$epsilon", "hello", 1),
            (1, "a", "world", 2),
        ], 0, {2})
        fst_inverse = fst.inverse()
        assert fst_inverse.transform_all("helloworld") == {"a"}

    def test_range_input_output(self) -> None:
        fst = create_fst([
            (0, "a--z", "$self", 1),
            (1, "a--b", "x", 3),
        ], 0, {3})
        fst_inverse = fst.inverse()
        assert fst_inverse.transform_all("x") == set()
        assert fst_inverse.transform_all("ax") == {"aa", "ab"}

    def test_range_input_string_output(self) -> None:
        fst = create_fst([
            (0, "a--z", "$self", 1),
            (1, "a--b", "xyz", 3),
        ], 0, {3})
        fst_inverse = fst.inverse()
        assert fst_inverse.transform_all("xyz") == set()
        assert fst_inverse.transform_all("ax") == set()
        assert fst_inverse.transform_all("axyz") == {"aa", "ab"}

    def test_epsilon_output(self) -> None:
        fst = compression_FST("a")
        fst_inverse = fst.inverse()
        nfa = create_nfa("a")
        expected = create_nfa("a+")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equal(expected, actual)
        nfa = create_nfa("aa+")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert actual.isEmpty()
        nfa = create_nfa("bab")
        expected = create_nfa("ba+b")
        actual = product_fst_automaton(fst_inverse, nfa)
        print("fst: ", fst_inverse)
        print("nfa: ", nfa)
        print("result: ", actual)
        print(diff(actual, expected))
        assert_equal(expected, actual)

    def test_cut_field_fst(self) -> None:
        fst = correct_cut_field_FST(" ", [3])
        fst_inverse = fst.inverse()
        nfa = create_nfa("a* b* c* d*")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert actual.isEmpty()
        nfa = create_nfa("x")
        expected = create_nfa("x|[^ ]* [^ ]* x( .*)?")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equal(expected, actual)
        nfa = create_nfa("a*b*c+")
        expected = create_nfa("a*b*c+|[^ ]* [^ ]* a*b*c+( .*)?")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equal(expected, actual)

    def test_start_regex_replacement_FST(self) -> None:
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
        assert_equal(expected, actual)

        fst = start_regex_replacement_FST(create_nfa("a.*b"), "x")
        fst_inverse = fst.inverse()
        nfa = create_nfa("a*b*")
        expected = create_nfa("a*|b*")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equal(expected, actual)
        nfa = create_nfa("x|a*b*")
        expected = create_nfa("a*b*|a.*b|x")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equal(expected, actual)

        fst = start_regex_replacement_FST(create_nfa("a.*b"), "xyz")
        fst_inverse = fst.inverse()
        nfa = create_nfa("a*b*")
        expected = create_nfa("a*|b*")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equal(expected, actual)
        nfa = create_nfa("xyz|a*b*")
        expected = create_nfa("a*b*|a.*b|xyz")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equal(expected, actual)

    def test_string_replacement_fst(self) -> None:
        fst = global_replacement_FST("ababc", "xyxyz")
        fst_inverse = fst.inverse()
        nfa = create_nfa("abababababc")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert actual.isEmpty()
        nfa = create_nfa("xyxyxyz")
        expected = create_nfa("xy(ababc|xyxyz)")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equal(expected, actual)
        nfa = create_nfa("xyxyxyxyxyxyxyxyz")
        expected = create_nfa("xyxyxyxyxyxy(ababc|xyxyz)")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equal(expected, actual)
        nfa = create_nfa("abab(x*y*)*z*")
        expected = create_nfa("abab(x*y*)*z*|abab(x*y*)*ababcz*")
        actual = product_fst_automaton(fst_inverse, nfa)
        assert_equal(expected, actual)
    
        

if __name__ == "__main__":
    pytest.main([__file__])
    jpype.shutdownJVM()