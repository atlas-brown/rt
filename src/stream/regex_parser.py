import re
from typing import TYPE_CHECKING, Optional

import jpype

if TYPE_CHECKING:
    from stream.regular_type import RegularType

from stream.java_api import Automaton, BasicAutomata, BasicOperations, RegExp


class Node:
    pass

class EmptyLanguageNode(Node):
    def __repr__(self):
        return "EmptyLanguageNode()"

class Literal(Node):
    def __init__(self, char: str):
        self.char = char
    def __repr__(self):
        return f"Literal({self.char!r})"

class Dot(Node):
    def __repr__(self):
        return "Dot()"

class Concatenate(Node):
    def __init__(self, nodes: list[Node]):
        self.nodes = nodes
    def __repr__(self):
        return f"Concatenate({self.nodes})"

class Repeat(Node):
    def __init__(self, node: Node, min_times: int, max_times: int | None):
        self.node = node
        self.min = min_times
        self.max = max_times
    def __repr__(self):
        return f"Repeat({self.node}, {self.min}, {self.max})"

class Range(Node):
    def __init__(self, start: str, end: str):
        self.start = start
        self.end = end
    def __repr__(self):
        return f"Range({self.start!r}-{self.end!r})"
    
class PosixClass(Node):
    def __init__(self, name: str):
        self.name = name
    def __repr__(self):
        return f"PosixClass({self.name!r})"

class CharacterClass(Node):
    def __init__(self, negate: bool, items: list[Literal | Range | PosixClass]):
        self.negate = negate
        self.items = items
    def __repr__(self):
        return f"CharacterClass(negate={self.negate}, items={self.items})"

class Intersection(Node):
    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"Intersection({self.left}, {self.right})"

class Complement(Node):
    def __init__(self, node: Node):
        self.node = node
    def __repr__(self):
        return f"Complement({self.node})"

class Union(Node):
    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"Union({self.left}, {self.right})"

class StartAnchor(Node):
    def __repr__(self):
        return "StartAnchor()"

class EndAnchor(Node):
    def __repr__(self):
        return "EndAnchor()"

class Hole(Node):
    def __init__(self, name: str):
        self.name = name
    def __repr__(self):
        return f"Hole({self.name!r})"

class RegexParser:
    def __init__(self, pattern, mode="compat"):
        self.pattern = pattern
        self.pos = 0
        self.length = len(pattern)
        if mode not in ("extended", "compat", "basic"):
            raise ValueError("Mode must be 'basic', 'extended', or 'compat'")
        self.mode = mode

    def current(self):
        if self.pos < self.length:
            return self.pattern[self.pos]
        return None

    def peek_next(self):
        if self.pos + 1 < self.length:
            return self.pattern[self.pos + 1]
        return None

    def consume(self, ch=None):
        if self.pos < self.length:
            cur = self.pattern[self.pos]
            if ch is not None and cur != ch:
                self.error(f"Expected '{ch}' at position {self.pos}, but got '{cur}'")
            self.pos += 1
            return cur
        return None

    def error(self, msg):
        raise ValueError(msg + f" pattern: {self.pattern}")

    def parse(self):
        node = self.parse_union_expr()
        if self.pos != self.length:
            self.error(f"Extra characters found at position {self.pos}: {self.pattern[self.pos:]}")
        return node

    def parse_union_expr(self):
        node = self.parse_intersect_expr()
        if self.mode in ("compat", "extended"):
            while self.current() == '|':
                self.consume('|')
                right = self.parse_intersect_expr()
                node = Union(node, right)
        else:
            while self.current() == '\\' and self.peek_next() == '|':
                self.consume('\\')
                self.consume('|')
                right = self.parse_intersect_expr()
                node = Union(node, right)
        return node

    def parse_intersect_expr(self):
        if self.mode == "compat":
            node = self.parse_concat_expr()
            while self.current() == '&':
                self.consume('&')
                right = self.parse_concat_expr()
                node = Intersection(node, right)
            return node
        else:
            return self.parse_concat_expr()

    def parse_concat_expr(self):
        nodes = []
        while self.pos < self.length and not self._concat_terminator():
            node = self.parse_repetition_expr()
            if node is not None:
                nodes.append(node)
            else:
                break
        if not nodes:
            return Literal("")
        if len(nodes) == 1:
            return nodes[0]
        return Concatenate(nodes)
    
    def _concat_terminator(self):
        cur = self.current()
        if self.mode == "compat":
            return cur in [')', '|', '&']
        elif self.mode == "extended":
            return cur in [')', '|']
        else:
            if cur == '\\' and self.peek_next() == '|':
                return True
            return False

    def parse_repetition_expr(self):
        node = self.parse_unary_expr()
        if self.mode in ("compat", "extended"):
            while True:
                curr = self.current()
                if curr is not None and curr in ('*', '+', '?'):
                    op = self.consume()
                    if op == '*':
                        node = Repeat(node, 0, None)
                    elif op == '+':
                        node = Repeat(node, 1, None)
                    elif op == '?':
                        node = Repeat(node, 0, 1)
                elif curr == '{' and self.peek_next() != '{':
                    min_val, max_val = self.parse_braced_quantifier(escaped=False)
                    node = Repeat(node, min_val, max_val)
                else:
                    break
            return node
        else:
            while True:
                curr = self.current()
                if curr == '*':
                    self.consume('*')
                    node = Repeat(node, 0, None)
                elif curr == '\\' and self.peek_next() in ['+', '?', '{']:
                    self.consume('\\')
                    op = self.consume()
                    if op == '+':
                        node = Repeat(node, 1, None)
                    elif op == '?':
                        node = Repeat(node, 0, 1)
                    elif op == '{':
                        min_val, max_val = self.parse_braced_quantifier(escaped=True)
                        node = Repeat(node, min_val, max_val)
                else:
                    break
            return node

    def parse_braced_quantifier(self, escaped=False):
        if not escaped:
            self.consume('{')
        num_str = ''
        while self.current() is not None and self.current().isdigit():
            num_str += self.consume()
        if num_str == '':
            self.error("Missing number in quantifier")
        min_val = int(num_str)
        max_val = min_val
        if self.current() == ',':
            self.consume(',')
            num_str = ''
            while self.current() is not None and self.current().isdigit():
                num_str += self.consume()
            if num_str == '':
                max_val = None
            else:
                max_val = int(num_str)
        if escaped:
            if not (self.current() == '\\' and self.peek_next() == '}'):
                self.error("Quantifier in basic mode must end with '\\}'")
            else:
                self.consume('\\')
                self.consume('}')
        else:
            if self.current() != '}':
                self.error("Quantifier must end with '}'")
            self.consume('}')
        return (min_val, max_val)

    def parse_unary_expr(self):
        if self.mode == "compat" and self.current() == '~':
            self.consume('~')
            if self.pos >= self.length or self.current() in [')', '|', '&']:
                return Complement(Literal(""))
            else:
                node = self.parse_unary_expr()
                return Complement(node)
        else:
            return self.parse_primary()

    def parse_hole(self):
        self.consume('{')
        if self.current() != '{':
            self.error("Expected '{{' for hole")
        self.consume('{')
        name = ""
        while self.current() is not None and not (self.current() == '}' and self.peek_next() == '}'):
            name += self.consume()
        if self.current() is None:
            self.error("Unterminated hole, expected '}}'")
        self.consume('}')
        if self.current() != '}':
            self.error("Expected '}}' to close hole")
        self.consume('}')
        return Hole(name)

    def parse_primary(self):
        curr = self.current()
        if curr is None:
            self.error("Unexpected end of expression")
        if self.mode == "compat" and curr == '{' and self.peek_next() == '{':
            return self.parse_hole()
        if self.mode in ("compat", "extended"):
            if curr == '(':
                self.consume('(')
                node = self.parse_union_expr()
                if self.current() != ')':
                    self.error("Missing closing parenthesis ')'")
                self.consume(')')
                return node
            elif curr == '[':
                return self.parse_character_class()
            elif curr == '.':
                self.consume('.')
                return Dot()
            elif curr == '^':
                self.consume('^')
                return StartAnchor()
            elif curr == '$':
                self.consume('$')
                return EndAnchor()
            elif curr == '\\':
                return Literal(self.parse_escape())
            else:
                return Literal(self.consume())
        else:
            if curr == '\\' and self.peek_next() == '(':
                self.consume('\\')
                self.consume('(')
                node = self._parse_basic_group()
                return node
            elif curr == '[':
                return self.parse_character_class()
            elif curr == '.':
                self.consume('.')
                return Dot()
            elif curr == '^':
                self.consume('^')
                return StartAnchor()
            elif curr == '$':
                self.consume('$')
                return EndAnchor()
            elif curr == '\\':
                return Literal(self.parse_escape())
            else:
                return Literal(self.consume())

    def _parse_basic_group(self):
        content = ""
        group_level = 1
        while self.pos < self.length:
            if self.current() == '\\' and self.peek_next() == '(':
                group_level += 1
                content += self.consume()
                content += self.consume()
            elif self.current() == '\\' and self.peek_next() == ')':
                group_level -= 1
                self.consume()
                self.consume()
                if group_level == 0:
                    break
                else:
                    content += "\\)"
            else:
                content += self.consume()
        if group_level != 0:
            self.error("Missing closing escaped ')' for group in basic mode")
        subparser = RegexParser(content, mode="basic")
        return subparser.parse()

    def parse_escape(self):
        self.consume('\\')
        curr = self.current()
        if curr is None:
            self.error("Escape character '\\' at end of expression")
        escape_dict = {
            'n': '\n',
            't': '\t',
            'r': '\r',
            'v': '\v',
            'f': '\f',
            'b': '\b',
            's': ' ',
            '+': '+',
            '{': '{',
            '}': '}',
            '|': '|',
            '&': '&',
            '~': '~',
            '*': '*',
            '?': '?',
            '.': '.',
            '^': '^',
            '$': '$',
            '(': '(',
            ')': ')',
            '[': '[',
            ']': ']',
            '\\': '\\'
        }
        if curr in escape_dict:
            self.consume()
            return escape_dict[curr]
        else:
            return self.consume()

    def parse_character_class(self):
        self.consume('[')
        negate = False
        if self.current() == '^':
            negate = True
            self.consume('^')
        items = []
        
        # Handle the special case: ']' as the first character in compat/extended mode
        if self.current() == ']':
            items.append(Literal(self.consume(']')))

        while self.current() is not None and self.current() != ']':
            if self.current() == '[' and self.peek_next() == ':':
                posix_item = self.parse_posix_class()
                items.append(posix_item)
            else:
                if self.current() == '\\':
                    start_char = self.parse_escape()
                else:
                    start_char = self.consume()
                if self.current() == '-' and self.peek_next() not in (']', None):
                    self.consume('-')
                    if self.current() == '\\':
                        end_char = self.parse_escape()
                    else:
                        end_char = self.consume()
                    items.append(Range(start_char, end_char))
                else:
                    items.append(Literal(start_char))
        if self.current() != ']':
            self.error("Unterminated character class; missing ']'")
        self.consume(']')
        return CharacterClass(negate, items)

    def parse_posix_class(self):
        self.consume('[')
        self.consume(':')
        name = ""
        while True:
            if self.current() is None:
                self.error("Unterminated POSIX character class; missing ':]'")
            if self.current() == ':' and self.peek_next() == ']':
                self.consume(':')
                self.consume(']')
                break
            else:
                name += self.consume()
        allowed = {"upper", "lower", "alpha", "digit", "xdigit", "alnum",
                   "punct", "blank", "space", "cntrl", "graph", "print"}
        if name not in allowed:
            self.error(f"Unknown POSIX character class: {name}")
        return PosixClass(name)

def get_prec(node):
    if isinstance(node, Union):
        return 1
    elif isinstance(node, Intersection):
        return 2
    elif isinstance(node, Concatenate):
        return 3
    elif isinstance(node, Repeat):
        return 4
    elif isinstance(node, Complement):
        return 5
    elif isinstance(node, Hole):
        return 6
    else:
        return 6

def escape_literal(ch):
    meta = "^$.*+?{}[]()|&~\\"
    if ch in meta:
        return "\\" + ch
    return ch

def escape_char_class(ch):
    if ch in "\\]":
        return "\\" + ch
    return ch
    

def ast_to_regex(ast):
    def _ast_to_regex(node, parent_prec=0):
        my_prec = get_prec(node)
        if isinstance(node, EmptyLanguageNode):
            return "∅"
        elif isinstance(node, Literal):
            if node.char == "":
                s = "()"
            else:
                s = escape_literal(node.char)
        elif isinstance(node, Dot):
            s = "."
        elif isinstance(node, Concatenate):
            s = "".join(_ast_to_regex(child, get_prec(node)) for child in node.nodes)
        elif isinstance(node, Repeat):
            base = _ast_to_regex(node.node, get_prec(node))
            if node.min == 0 and node.max is None:
                quant = "*"
            elif node.min == 1 and node.max is None:
                quant = "+"
            elif node.min == 0 and node.max == 1:
                quant = "?"
            elif node.max is None:
                quant = "{" + str(node.min) + ",}"
            elif node.min == node.max:
                quant = "{" + str(node.min) + "}"
            else:
                quant = "{" + str(node.min) + "," + str(node.max) + "}"
            s = base + quant
        elif isinstance(node, CharacterClass):
            s = "["
            if node.negate:
                s += "^"
            for item in node.items:
                if isinstance(item, Range):
                    s += escape_char_class(item.start) + "-" + escape_char_class(item.end)
                elif isinstance(item, PosixClass):
                    s += "[:{}:]".format(item.name)
                elif isinstance(item, Literal):
                    s += escape_char_class(item.char)
                else:
                    s += _ast_to_regex(item)
            s += "]"
        elif isinstance(node, Intersection):
            left = _ast_to_regex(node.left, get_prec(node))
            right = _ast_to_regex(node.right, get_prec(node)+1)
            s = left + "&" + right
        elif isinstance(node, Complement):
            s = "~" + _ast_to_regex(node.node, get_prec(node))
        elif isinstance(node, Union):
            left = _ast_to_regex(node.left, get_prec(node))
            right = _ast_to_regex(node.right, get_prec(node)+1)
            s = left + "|" + right
        elif isinstance(node, StartAnchor):
            s = "^"
        elif isinstance(node, EndAnchor):
            s = "$"
        elif isinstance(node, Hole):
            s = f"{{{{{node.name}}}}}"
        else:
            s = ""
        if my_prec < parent_prec:
            return "(" + s + ")"
        else:
            return s
    return _ast_to_regex(ast, 0)


def ast_to_automaton(node: Node, hole_dict: Optional[dict[str, Automaton]] = None) -> Automaton:
    def _ast_to_automaton(node: Node, hole_dict: Optional[dict[str, Automaton]] = None) -> Automaton:
        if hole_dict is None:
            hole_dict = {}

        if isinstance(node, EmptyLanguageNode):
            return BasicAutomata.makeEmpty()
        elif isinstance(node, Literal):
            if node.char == "":
                return BasicAutomata.makeEmptyString()
            return BasicAutomata.makeChar(node.char)
        elif isinstance(node, Dot):
            return BasicAutomata.makeAnyChar()
        elif isinstance(node, Concatenate):
            children = jpype.JClass("java.util.ArrayList")()
            for child in node.nodes:
                children.add(ast_to_automaton(child, hole_dict))
            return BasicOperations.concatenate(children)
        elif isinstance(node, Repeat):
            base = ast_to_automaton(node.node, hole_dict)
            if node.max is None:
                return BasicOperations.repeat(base, node.min)
            return BasicOperations.repeat(base, node.min, node.max)
        elif isinstance(node, CharacterClass):
            children = jpype.JClass("java.util.ArrayList")()
            for item in node.items:
                children.add(ast_to_automaton(item, hole_dict))
            if node.negate:
                return BasicOperations.minus(BasicAutomata.makeAnyChar(), BasicOperations.union(children))
            return BasicOperations.union(children)
        elif isinstance(node, Range):
            return BasicAutomata.makeCharRange(node.start, node.end)
        elif isinstance(node, Intersection):
            return BasicOperations.intersection(ast_to_automaton(node.left, hole_dict), ast_to_automaton(node.right, hole_dict))
        elif isinstance(node, Complement):
            return BasicOperations.minus(BasicAutomata.makeAnyString(), ast_to_automaton(node.node, hole_dict))
        elif isinstance(node, Union):
            return BasicOperations.union(ast_to_automaton(node.left, hole_dict), ast_to_automaton(node.right, hole_dict))
        elif isinstance(node, StartAnchor):
            return BasicAutomata.makeEmptyString()
        elif isinstance(node, EndAnchor):
            return BasicAutomata.makeEmptyString()
        elif isinstance(node, Hole):
            if node.name in hole_dict:
                return hole_dict[node.name]
            else:
                raise ValueError(f"Hole '{node.name}' not provided in hole_dict")
        elif isinstance(node, PosixClass):
            name = node.name
            if name == "upper":
                return RegExp("[A-Z]").toAutomaton()
            elif name == "lower":
                return RegExp("[a-z]").toAutomaton()
            elif name == "alpha":
                return RegExp("[A-Za-z]").toAutomaton()
            elif name == "digit":
                return RegExp("[0-9]").toAutomaton()
            elif name == "xdigit":
                return RegExp("[0-9A-Fa-f]").toAutomaton()
            elif name == "alnum":
                return RegExp("[A-Za-z0-9]").toAutomaton()
            elif name == "punct":
                return RegExp("[!-/:-@[-`{-~]").toAutomaton()
            elif name == "blank":
                return RegExp("[ \t]").toAutomaton()
            elif name == "space":
                return RegExp("[ \t\n\r\v\f]").toAutomaton()
            elif name == "cntrl":
                return BasicOperations.union(BasicAutomata.makeCharRange(chr(0), chr(31)), BasicAutomata.makeChar(chr(127)))
            elif name == "graph" or name == "print":
                return BasicAutomata.makeCharRange(chr(33), chr(126))
            else:
                raise ValueError(f"Unknown POSIX character class: {name}")
        else:
            raise ValueError(f"Unknown node type: {node}")
    automaton = _ast_to_automaton(node, hole_dict)
    automaton.setDeterministic(False)
    automaton.removeDeadTransitions()
    automaton.minimize()
    return automaton


def is_pure_string(s: str, mode="compat") -> bool:
    node = RegexParser(s, mode=mode).parse()
    return is_pure_string_for_ast(node)


def is_pure_string_for_ast(ast: Node) -> bool:
    if isinstance(ast, Literal):
        return True
    elif isinstance(ast, Concatenate):
        return all(is_pure_string_for_ast(child) for child in ast.nodes)
    elif isinstance(ast, CharacterClass):
        if ast.negate:
            return False
        if len(ast.items) == 1 and isinstance(ast.items[0], Literal):
            return True
    return False

def convert_to_pure_string(s: str, mode="compat") -> Optional[str]:
    return convert_to_pure_string_for_ast(RegexParser(s, mode=mode).parse())

def convert_to_pure_string_for_ast(ast: Node) -> Optional[str]:
    if not is_pure_string_for_ast(ast):
        return None
    def _convert_to_pure_string(node) -> str:
        if isinstance(node, Literal):
            return node.char
        elif isinstance(node, Concatenate):
            return "".join(_convert_to_pure_string(child) for child in node.nodes)
        elif isinstance(node, CharacterClass):
            return node.items[0].char
        return None
    return _convert_to_pure_string(ast)

def preprocess(pattern: str | None) -> str:
    if pattern is None:
        pattern = ""
    replace_pattern = r'\$\{[^}]*\}|\$\([^)]*\)|\\\$\\\{[^}]*\\\}|\\\$\\\([^)]*\\\)'
    pattern = re.sub(replace_pattern, r'(.*)', pattern)
    replace_pattern = r'\(\?!'
    pattern = re.sub(replace_pattern, r'~(', pattern)
    return pattern


def starts_with_start_anchor(pattern: "RegularType") -> bool:
    if pattern.ast is None:
        return False
    if isinstance(pattern.ast, Concatenate):
        return isinstance(pattern.ast.nodes[0], StartAnchor)
    return False


def ends_with_end_anchor(pattern: "RegularType") -> bool:
    if pattern.ast is None:
        return False
    if isinstance(pattern.ast, Concatenate):
        return isinstance(pattern.ast.nodes[-1], EndAnchor)
    return False


def remove_anchors(pattern: "RegularType") -> "RegularType":
    if pattern.ast is None:
        return pattern
    if isinstance(pattern.ast, Concatenate):
        if isinstance(pattern.ast.nodes[0], StartAnchor):
            pattern.ast.nodes = pattern.ast.nodes[1:]
        if isinstance(pattern.ast.nodes[-1], EndAnchor):
            pattern.ast.nodes = pattern.ast.nodes[:-1]
    return pattern


def has_backreference(text: str) -> bool:
    return re.search(r'(?<!\\)(?:\\\\)*\\[1-9]', text) is not None


def has_basic_capture_group(pattern: str) -> bool:
    return "\\(" in pattern or "\\)" in pattern


def escape_literal_for_regular_type(string: str) -> str:
    return (
        re.escape(string)
        .replace("\\$", "[$]")
        .replace("\\{", "[{]")
        .replace("\\}", "[}]")
    )


def build_character_class(chars: str) -> str:
    escaped_chars = []
    seen = set()
    for ch in chars:
        if ch in seen:
            continue
        seen.add(ch)
        if ch == "\n":
            escaped = "\\n"
        elif ch == "\t":
            escaped = "\\t"
        elif ch == "\r":
            escaped = "\\r"
        elif ch == "\\":
            escaped = "\\\\"
        elif ch == "-":
            escaped = "\\-"
        elif ch == "]":
            escaped = "\\]"
        elif ch == "^":
            escaped = "\\^"
        else:
            escaped = re.escape(ch)
        escaped_chars.append(escaped)
    return "".join(escaped_chars)


if __name__ == "__main__":
    pattern = "~(.*{{a}}.*)&(a{1,3}{{b}}[ab-e[:digit:]]{3,10}[^ab])+[]+a-z]"
    mode = "compat"
    hole_dict = {
        "a": RegExp("aa").toAutomaton(),
        "b": RegExp("b").toAutomaton(),
    }
    if mode == "":
        mode = "compat"
    parser = RegexParser(pattern, mode=mode)
    ast = parser.parse()
    print("Generated AST:")
    print(ast)
    ext_regex = ast_to_regex(ast)
    print("\nTranslated Regex:")
    print(ext_regex)
    automaton = ast_to_automaton(ast, hole_dict)
    print("\nAutomaton:")
    print(automaton)
    shortest = automaton.getShortestExample(True)
    print(f"\nShortest Example: {shortest!r}")
    print(ord(shortest[0]))
    print(ord(shortest[-1]))
