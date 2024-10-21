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
    assert preprocess("{[0-9]+}&{[0-9a-z]+}") == "(?!(?![0-9]+)|(?![0-9a-z]+))"
    assert preprocess("(?!{[0-9]+}&{[0-9a-z]+})") == "(?!(?!(?![0-9]+)|(?![0-9a-z]+)))"
    assert preprocess("(?!{{A}&{B}}&{{C}&{D}})") == "(?!(?!(?!(?!(?!A)|(?!B)))|(?!(?!(?!C)|(?!D)))))"
    assert preprocess("{A}&{B\\}}") == "(?!(?!A)|(?!B\\}))"
    assert preprocess("{\\{A}&{B}ab") == "(?!(?!\\{A)|(?!B))ab"


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
    run_inre_tests("(?!{(.*0.*)}&{(()|(.*\\W))0(()|(\\W.*)}))",
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

    