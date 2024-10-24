import z3
from stream.regex_to_z3 import regex_to_z3_expr
import sre_parse
import logging

class RegularType:
    def __init__(self, pattern: str):
        self.pattern = pattern
    
    def is_subtype(self, other: 'RegularType') -> bool:
        logging.debug(f"checking: {self.pattern} is subtype of {other.pattern}")
        s = z3.Solver()
        x = z3.String('x')
        self_regex = regex_to_z3_expr(sre_parse.parse(preprocess(self.pattern)))
        logging.debug(f"self_regex: {self_regex}")
        other_regex = regex_to_z3_expr(sre_parse.parse(preprocess(other.pattern)))
        logging.debug(f"other_regex: {other_regex}")
        logging.debug("------------------------------")
        intersection_regex = z3.Intersect(self_regex, z3.Complement(other_regex))
        s.add(z3.InRe(x, intersection_regex))
        result = s.check() == z3.unsat
        if not result:
            logging.debug(f"counterexample: {s.model()}")
        return result
    
    def __le__(self, other: 'RegularType') -> bool:
        return self.is_subtype(other)
    
    def __repr__(self) -> str:
        return f"RegularType({self.pattern})"
            
# provisioanl implementation
# intersection {A}&{B} -> (?!(?!A)|(?!B)) by De Morgan's law
# Q: Why dont directly use z3.Intersect e.g., return Z3.Intersect(A, B) directly instead of (?!A)|(?!B)
# A: If there are operations out of the intersection, it will be problematic, e.g., (?!{A}&{B})
def preprocess(pattern: str) -> str:
    if "}&{" not in pattern:
        return pattern
    

    intersect_index = pattern.index("}&{")
    # find { in the left side
    left_index = intersect_index
    open_brackets = 1
    while left_index >= 1 and open_brackets > 0:
        left_index -= 1
        if pattern[left_index] == "}" and (left_index == 0 or pattern[left_index-1] != "\\"):
            open_brackets += 1
        elif pattern[left_index] == "{" and (left_index == 0 or pattern[left_index-1] != "\\"):
            open_brackets -= 1
    
    if open_brackets != 0:
        raise Exception("unmatched brackets at the left side of the intersection")

    assert pattern[left_index] == "{"
    
    # find } in the right side
    right_index = intersect_index + 2
    open_brackets = 1
    while right_index < len(pattern) - 1 and open_brackets > 0:
        right_index += 1
        if pattern[right_index] == "{" and pattern[right_index-1] != "\\":
            open_brackets += 1
        elif pattern[right_index] == "}" and pattern[right_index-1] != "\\":
            open_brackets -= 1

    if open_brackets != 0:
        raise Exception("unmatched brackets at the right side of the intersection")

    assert pattern[right_index] == "}"

    left = pattern[left_index+1:intersect_index]
    right = pattern[intersect_index+3:right_index]
    left_rest = pattern[:left_index]
    right_rest = pattern[right_index+1:]

    # }&{ number reduces, so the recursive call will eventually terminate
    return preprocess(f"{left_rest}(?!(?!{left})|(?!{right})){right_rest}")
    

        

        
        
