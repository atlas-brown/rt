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
        self_regex = translate_to_z3_regex(self.pattern)
        other_regex = translate_to_z3_regex(other.pattern)
        intersection_regex = z3.Intersect(self_regex, z3.Complement(other_regex))
        s.add(z3.InRe(x, intersection_regex))
        return s.check() == z3.unsat
    
    def __le__(self, other: 'RegularType') -> bool:
        return self.is_subtype(other)
    
    def __repr__(self) -> str:
        return f"RegularType({self.pattern})"
    
def translate_to_z3_regex(pattern: str) -> z3.ReRef:
    if len(pattern) == 0:
        return z3.Re('')
    parts = pattern.split('&')
    if len(parts) == 1:
        return regex_to_z3_expr(sre_parse.parse(pattern))
    else:
        return z3.Intersect(*[translate_to_z3_regex(part) for part in parts])