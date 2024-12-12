from typing import List
from stream.regular_type import preprocess, RegularType
import z3
from stream.regex_to_z3 import regex_to_z3_expr
import sre_parse

def test_preprocess():
    assert preprocess("a") == "a"
    assert preprocess("[0-9]") == "[0-9]"
    assert preprocess("[0-9]+") == "[0-9]+"
    assert preprocess(".*") == ".*"
    assert preprocess("([0-9]+)&([0-9a-z]+)") == "(?!(?![0-9]+)|(?![0-9a-z]+))"
    assert preprocess("(?!([0-9]+)&([0-9a-z]+))") == "(?!(?!(?![0-9]+)|(?![0-9a-z]+)))"
    assert preprocess("(?!((A)&(B))&((C)&(D)))") == "(?!(?!(?!(?!(?!A)|(?!B)))|(?!(?!(?!C)|(?!D)))))"
    assert preprocess("(A)&(B\\})") == "(?!(?!A)|(?!B\\}))"
    assert preprocess("(\\{A)&(B)ab") == "(?!(?!\\{A)|(?!B))ab"


def run_inre_tests(regex: str, postive: List[str], negative: List[str]):
    regex = regex_to_z3_expr(sre_parse.parse(preprocess(regex)))
    for p in postive:
        print("checking positive example: ", p)
        s = z3.Solver()
        s.add(z3.InRe(z3.StringVal(p), regex))
        assert s.check() == z3.sat
    
    for n in negative:
        print("checking negative example: ", n)
        s = z3.Solver()
        s.add(z3.InRe(z3.StringVal(n), regex))
        assert s.check() == z3.unsat

def test_any():
    run_inre_tests(".", ["a", "1", "2", "3", "4", "5", " ", "b", "0", "c", "9", "0", "2", "2", "0"], ["a12345", "b0c9", "02", "20", ""])
    run_inre_tests(".*", ["a", "12345", " ", "a12345", "b0c9", "02", "20"], [])
    run_inre_tests(".+", ["a", "12345", " ", "a12345", "b0c9", "02", "20"], [""])
    run_inre_tests(".?", ["a", "", " "], ["a12345", "b0c9", "02", "20"])


def test_union():
    run_inre_tests("A|B", ["A", "B"], ["C", "AB", "BA"])
    run_inre_tests("A|B|C", ["A", "B", "C"], ["D", "AB", "BA", "AC", "CA", "BC", "CB"])

def test_negation():
    run_inre_tests("(?!A)", ["B", "C", "D", "AB", "BA", "AC", "CA", "BC", "CB"], ["A"])
    run_inre_tests("(?!A|B)", ["C", "D", "AB"], ["A", "B"])

def test_negation_1():
    examples = ["a12345", "", ".*", ".+", ".?", ".", "(?!.*0.*)", "(()|(.*\\W))0", "(?!(()|(.*\\W))0(()|(\\W.*)))", "(?!((.*0.*))&((()|(.*\\W))0(()|(\\W.*))))"]
    # for every example, the intersection with itself should be empty
    for e in examples:
        s = z3.Solver()
        regex = regex_to_z3_expr(sre_parse.parse(preprocess(e)))
        x = z3.String('x')
        s.add(z3.InRe(x, z3.Intersect(regex, z3.Complement(regex))))
        assert s.check() == z3.unsat
    # for every example, the double negation should be equivalent to the original
    for e in examples:
        s = z3.Solver()
        regex = regex_to_z3_expr(sre_parse.parse(preprocess(e)))
        x = z3.String('x')
        s.add(z3.InRe(x, regex) != z3.InRe(x, z3.Complement(z3.Complement(regex))))
        assert s.check() == z3.unsat


def test_grep_vE():
    run_inre_tests("(?!.*0.*)", ["a12345", "", " "], ["b0c9", "02", "20", "0", "1 0"])

def test_grep_vwE_2():
    run_inre_tests("(()|(.*\\W))0",
                [
                    "a 0",
                    " 0",
                    "0",
                    "-0",
                    "1-0"
                ],
                [
                    "a12345",
                    "b0c9",
                    "02",
                    "20",
                    "0 a",
                    "0 ",
                    "a 0 a",
                    "0+",
                ])

def test_grep_vwE_1():
    run_inre_tests("(?!(()|(.*\\W))0(()|(\\W.*)))",
                [
                    "a12345",
                    "b0c9",
                    "02",
                    "20"
                ],
                [
                    "0 a",
                    "a 0",
                    " 0",
                    "0 ",
                    "a 0 a",
                    "0",
                    "0+",
                    "-0",
                    "1-0"
                ])
    


def test_grep_vwE_translation():
    run_inre_tests("(?!((.*0.*))&((()|(.*\\W))0(()|(\\W.*))))",
                [
                    "a12345",
                    "b0c9",
                    "02",
                    "20"
                ],
                [
                    "0 a",
                    "a 0",
                    " 0",
                    "0 ",
                    "a 0 a",
                    "0",
                    "0+",
                    "-0",
                    "1-0"
                ])

    