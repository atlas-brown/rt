import re
import z3
from stream.regex_to_z3 import regex_to_z3_expr
import sre_parse
import logging
from stream.checking_result import CheckingResult
from stream.timeout_util import run_with_timeout
from stream.tool_error import ToolError

class RegularType:
    def __init__(self, pattern: str):
        self.pattern = pattern
        self._regex = None

    def init_regex(self):
        if self._regex is None:
            self._regex = regex_to_z3_expr(sre_parse.parse(preprocess(self.pattern)))

    @property
    def regex(self):
        self.init_regex()
        return self._regex
    
    def is_subtype(self, other: 'RegularType') -> CheckingResult:
        logging.debug("-"*60)
        logging.debug(f"checking: {self.pattern} is subtype of {other.pattern}")
        logging.debug(f"self_regex: {self.regex}")
        logging.debug(f"other_regex: {other.regex}")
        logging.debug("-"*60)
        if (other.pattern == ".*"):
            return CheckingResult(False)
        s = z3.Solver()
        intersection_regex = z3.Intersect(self.regex, z3.Complement(other.regex))
        s.add(z3.Distinct(intersection_regex, z3.Intersect(z3.Re("a"), z3.Re("b"))))
        checking_result = CheckingResult(s.check() == z3.sat)
        if checking_result.ill_typed:
            s = z3.Solver()
            # s.set(max_memory=15)
            # s.set(timeout=20000)
            x = z3.String('x')
            s.add(z3.InRe(x, intersection_regex))
            s.check()
            counterexample = s.model()[x].as_string()
            checking_result.set_counterexample(counterexample)
        return checking_result
    
    # will throw TimeoutError if the function takes too long to run
    def is_subtype_with_timeout(self, other: 'RegularType', timeout: int) -> CheckingResult:
        self.init_regex()
        other.init_regex()
        return run_with_timeout(self.is_subtype, timeout, other)

    def is_empty(self) -> bool:
        s = z3.Solver()
        logging.debug(f"self_regex: {self.regex}")
        s.add(z3.Distinct(self.regex, z3.Intersect(z3.Re("a"), z3.Re("b"))))
        return s.check() == z3.unsat
    
    def is_empty_string(self) -> bool:
        s = z3.Solver()
        s.add(z3.Distinct(self.regex, z3.Re("")))
        return s.check() == z3.unsat

    def __le__(self, other: 'RegularType') -> bool:
        return self.is_subtype(other)
    
    def __repr__(self) -> str:
        return f"RegularType({self.pattern})"
            
# provisioanl implementation
# intersection (A)&(B) -> (?!(?!A)|(?!B)) by De Morgan's law
# Q: Why dont directly use z3.Intersect e.g., return Z3.Intersect(A, B) directly instead of (?!A)|(?!B)
# A: If there are operations out of the intersection, it will be problematic, e.g., (?!(A)&(B))

# replace ${A} with (.*)  and  $(A) with (.*)
def preprocess(pattern: str) -> str:
    # process replacement(${A} to (.*)) 
    # for $(), cannot handle nested brackets, need to be fixed
    replace_pattern = r'\$\{[^}]*\}|\$\([^)]*\)|\\\$\\\{[^}]*\\\}|\\\$\\\([^)]*\\\)'
    pattern = re.sub(replace_pattern, r'(.*)', pattern)


    if ")&(" not in pattern:
        return pattern
    

    intersect_index = pattern.index(")&(")
    # find ( in the left side
    left_index = intersect_index
    open_brackets = 1
    while left_index >= 1 and open_brackets > 0:
        left_index -= 1
        if pattern[left_index] == ")" and (left_index == 0 or pattern[left_index-1] != "\\"):
            open_brackets += 1
        elif pattern[left_index] == "(" and (left_index == 0 or pattern[left_index-1] != "\\"):
            open_brackets -= 1
    
    if open_brackets != 0:
        raise ToolError("unmatched brackets at the left side of the intersection")

    assert pattern[left_index] == "("
    
    # find ) in the right side
    right_index = intersect_index + 2
    open_brackets = 1
    while right_index < len(pattern) - 1 and open_brackets > 0:
        right_index += 1
        if pattern[right_index] == "(" and pattern[right_index-1] != "\\":
            open_brackets += 1
        elif pattern[right_index] == ")" and pattern[right_index-1] != "\\":
            open_brackets -= 1

    if open_brackets != 0:
        raise ToolError("unmatched brackets at the right side of the intersection")

    assert pattern[right_index] == ")"

    left = pattern[left_index+1:intersect_index]
    right = pattern[intersect_index+3:right_index]
    left_rest = pattern[:left_index]
    right_rest = pattern[right_index+1:]

    if is_dot_star(left):
        return preprocess(f"{left_rest}({right}){right_rest}")
    if is_dot_star(right):
        return preprocess(f"{left_rest}({left}){right_rest}")

    # )&( reduces, so the recursive call will eventually terminate
    return preprocess(f"{left_rest}(?!(?!{left})|(?!{right})){right_rest}")

def is_dot_star(s: str) -> bool:
    while len(s) > 0 and s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    return s == ".*"
    
    

        

        
        
