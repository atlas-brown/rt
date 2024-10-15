import z3
from regex_to_z3 import regex_to_z3_expr
import sre_parse

class RegularType:
    def __init__(self, pattern: str):
        self.pattern = pattern
    
    def is_subtype(self, other: 'RegularType') -> bool:
        print(f"checking: {self.pattern} is subtype of {other.pattern}")
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
    
# def translate_to_z3_regex(pattern: str) -> z3.ReRef:
    # need to be refined!!!!
    # handle case-insensitive prefix (?i)
    # case_insensitive = False
    # if pattern.startswith("(?i)"):
    #     case_insensitive = True
    #     pattern = pattern[4:]

    # regex_stack = []

    # token_pattern = re.compile(r'([a-zA-Z0-9]+|\*|\+|\?|.)')
    
    # tokens = token_pattern.findall(pattern)
    # i = 0
    # while i < len(tokens):
    #     token = tokens[i]
        
    #     match token:
    #         case '*':
    #             if regex_stack:
    #                 last = regex_stack.pop()
    #                 regex_stack.append(z3.Star(last))
    #             else:
    #                 raise ValueError("'*' cannot be the first token")
        
    #         case '+':
    #             if regex_stack:
    #                 last = regex_stack.pop()
    #                 regex_stack.append(z3.Plus(last))
    #             else:
    #                 raise ValueError("'+' cannot be the first token")
        
    #         case '?':
    #             if regex_stack:
    #                 last = regex_stack.pop()
    #                 regex_stack.append(z3.Union(last, z3.Re('')))
    #             else:
    #                 raise ValueError("'?' cannot be the first token")

    #         case '[':
    #             range_content = []
    #             i += 1
    #             while i < len(tokens) and tokens[i] != ']':
    #                 range_content.append(tokens[i])
    #                 i += 1
                
    #             if i == len(tokens) or tokens[i] != ']':
    #                 raise ValueError("Unmatched '[' in the regular expression")

    #             range_content = ''.join(range_content)

    #             if '-' in range_content and len(range_content) == 3:
    #                 start, end = range_content.split('-')
    #                 regex_stack.append(z3.Range(start, end))
    #             else:
    #                 union_parts = [z3.Re(char) for char in range_content]
    #                 regex_stack.append(z3.Union(*union_parts))
        
    #         case '.':
    #             regex_stack.append(z3.Range("\x00", "\x7F"))

    #         case _:
    #             if case_insensitive:
    #                 token = ''.join(f'[{char.lower()}{char.upper()}]' if char.isalpha() else char for char in token)
    #             regex_stack.append(z3.Re(token))
        
    #     i += 1

    # if len(regex_stack) > 1:
    #     result = regex_stack[0]
    #     for part in regex_stack[1:]:
    #         result = z3.Concat(result, part)
    # elif regex_stack:
    #     result = regex_stack[0]
    # else:
    #     result = z3.Re('')
    # print(f"{pattern} to {result}")
    # return result
