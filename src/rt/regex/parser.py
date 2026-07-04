from enum import Enum, auto

from . import ast


class ParseError(ValueError):
    pass


class Dialect(Enum):
    BRE = auto()
    ERE = auto()
    ERE_EXTENDED = auto()  # Supports complement, intersection, and holes


def parse_regex(regex: str, dialect: Dialect = Dialect.ERE_EXTENDED) -> ast.Regex:
    return Parser(regex, dialect).parse()


class Parser:
    def __init__(
        self,
        regex: str,
        dialect: Dialect = Dialect.ERE_EXTENDED,
    ):
        self.regex = regex
        self.pos = 0
        self.length = len(self.regex)
        self.dialect = dialect

    def parse(self) -> ast.Regex:
        node = self.parse_union_expr()
        if self.pos != self.length:
            self.error(
                f"Extra characters found at position {self.pos}: {self.regex[self.pos:]}"
            )
        return node

    def parse_union_expr(self):
        node = self.parse_intersect_expr()
        if self.dialect in (Dialect.ERE_EXTENDED, Dialect.ERE):
            while self.current() == "|":
                self.consume("|")
                right = self.parse_intersect_expr()
                node = ast.Union(node, right)
        else:
            while self.current() == "\\" and self.peek_next() == "|":
                self.consume("\\")
                self.consume("|")
                right = self.parse_intersect_expr()
                node = ast.Union(node, right)
        return node

    def parse_intersect_expr(self):
        if self.dialect == Dialect.ERE_EXTENDED:
            node = self.parse_concat_expr()
            while self.current() == "&":
                self.consume("&")
                right = self.parse_concat_expr()
                node = ast.Intersection(node, right)
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
            return ast.Epsilon()
        return self._make_concat(nodes)

    def _make_concat(self, nodes: list[ast.Regex]) -> ast.Regex:
        result = nodes[-1]
        for node in reversed(nodes[:-1]):
            result = ast.Concatenation(node, result)
        return result

    def _concat_terminator(self):
        cur = self.current()
        if self.dialect == Dialect.ERE_EXTENDED:
            return cur in [")", "|", "&"]
        elif self.dialect == Dialect.ERE:
            return cur in [")", "|"]
        else:
            if cur == "\\" and self.peek_next() == "|":
                return True
            return False

    def parse_repetition_expr(self):
        node = self.parse_unary_expr()
        if self.dialect in (Dialect.ERE_EXTENDED, Dialect.ERE):
            while True:
                curr = self.current()
                if curr is not None and curr in ("*", "+", "?"):
                    op = self.consume()
                    if op == "*":
                        node = ast.Repetition(node, min=0, max=None)
                    elif op == "+":
                        node = ast.Repetition(node, min=1, max=None)
                    elif op == "?":
                        node = ast.Repetition(node, min=0, max=1)
                elif curr == "{" and self.peek_next() != "{":
                    min_val, max_val = self.parse_braced_quantifier(escaped=False)
                    node = ast.Repetition(node, min=min_val, max=max_val)
                else:
                    break
            return node
        else:
            while True:
                curr = self.current()
                if curr == "*":
                    self.consume("*")
                    node = ast.Repetition(node, min=0, max=None)
                elif curr == "\\" and self.peek_next() in ["+", "?", "{"]:
                    self.consume("\\")
                    op = self.consume()
                    if op == "+":
                        node = ast.Repetition(node, min=1, max=None)
                    elif op == "?":
                        node = ast.Repetition(node, min=0, max=1)
                    elif op == "{":
                        min_val, max_val = self.parse_braced_quantifier(escaped=True)
                        node = ast.Repetition(node, min=min_val, max=max_val)
                else:
                    break
            return node

    def parse_braced_quantifier(self, escaped=False):
        if not escaped:
            self.consume("{")
        num_str = ""
        while (c := self.current()) is not None and c.isdigit():
            num_str += self.consume()
        if num_str == "":
            self.error("Missing number in quantifier")
        min_val = int(num_str)
        max_val = min_val
        if self.current() == ",":
            self.consume(",")
            num_str = ""
            while (c := self.current()) is not None and c.isdigit():
                num_str += self.consume()
            if num_str == "":
                max_val = None
            else:
                max_val = int(num_str)
        if escaped:
            if not (self.current() == "\\" and self.peek_next() == "}"):
                self.error("Quantifier in BRE mode must end with '\\}'")
            else:
                self.consume("\\")
                self.consume("}")
        else:
            if self.current() != "}":
                self.error("Quantifier must end with '}'")
            self.consume("}")
        return (min_val, max_val)

    def parse_unary_expr(self):
        if self.dialect == Dialect.ERE_EXTENDED and self.current() == "~":
            self.consume("~")
            if self.pos >= self.length or self.current() in [")", "|", "&"]:
                return ast.Complement(ast.Epsilon())
            else:
                node = self.parse_unary_expr()
                return ast.Complement(node)
        else:
            return self.parse_primary()

    def parse_hole(self):
        self.consume("{")
        if self.current() != "{":
            self.error("Expected '{{' for hole")
        self.consume("{")
        name = ""
        while self.current() is not None and not (
            self.current() == "}" and self.peek_next() == "}"
        ):
            name += self.consume()
        if self.current() is None:
            self.error("Unterminated hole, expected '}}'")
        self.consume("}")
        if self.current() != "}":
            self.error("Expected '}}' to close hole")
        self.consume("}")
        return ast.Hole(name.strip())

    def parse_primary(self):
        curr = self.current()
        if curr is None:
            self.error("Unexpected end of expression")
        if curr == "*":
            self.error("Dangling repetition operator '*' with no target")
        if (
            self.dialect == Dialect.ERE_EXTENDED
            and curr == "{"
            and self.peek_next() == "{"
        ):
            return self.parse_hole()
        if self.dialect in (Dialect.ERE_EXTENDED, Dialect.ERE):
            if curr == "(":
                self.consume("(")
                node = self.parse_union_expr()
                if self.current() != ")":
                    self.error("Missing closing parenthesis ')'")
                self.consume(")")
                return node
            elif curr == "[":
                return self.parse_character_class()
            elif curr == ".":
                self.consume(".")
                return ast.Dot()
            elif curr == "^":
                self.consume("^")
                return ast.StartAnchor()
            elif curr == "$":
                self.consume("$")
                return ast.EndAnchor()
            elif curr == "\\":
                return ast.Literal(self.parse_escape())
            else:
                ch = self.consume()
                return ast.Literal(ch)
        else:
            if curr == "\\" and self.peek_next() == "(":
                self.consume("\\")
                self.consume("(")
                node = self._parse_basic_group()
                return node
            elif curr == "[":
                return self.parse_character_class()
            elif curr == ".":
                self.consume(".")
                return ast.Dot()
            elif curr == "^":
                self.consume("^")
                return ast.StartAnchor()
            elif curr == "$":
                self.consume("$")
                return ast.EndAnchor()
            elif curr == "\\":
                return ast.Literal(self.parse_escape())
            else:
                ch = self.consume()
                return ast.Literal(ch)

    def _parse_basic_group(self):
        content = ""
        group_level = 1
        while self.pos < self.length:
            if self.current() == "\\" and self.peek_next() == "(":
                group_level += 1
                content += self.consume()
                content += self.consume()
            elif self.current() == "\\" and self.peek_next() == ")":
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
            self.error("Missing closing escaped ')' for group in BRE mode")
        subparser = Parser(
            content,
            dialect=Dialect.BRE,
        )
        return subparser.parse()

    def parse_escape(self) -> str:
        self.consume("\\")
        curr = self.current()
        if curr is None:
            self.error("Escape character '\\' at end of expression")
        escape_dict = {
            "n": "\n",
            "t": "\t",
            "r": "\r",
            "v": "\v",
            "f": "\f",
            "b": "\b",
            "s": " ",
            "+": "+",
            "{": "{",
            "}": "}",
            "|": "|",
            "&": "&",
            "~": "~",
            "*": "*",
            "?": "?",
            ".": ".",
            "^": "^",
            "$": "$",
            "(": "(",
            ")": ")",
            "[": "[",
            "]": "]",
            "\\": "\\",
        }
        if curr in escape_dict:
            self.consume()
            return escape_dict[curr]
        else:
            return self.consume()

    def parse_character_class(self):
        self.consume("[")
        negate = False
        if self.current() == "^":
            negate = True
            self.consume("^")
        items = []

        # Handle the special case: ']' as the first character in ere/ere_extended mode
        if self.current() == "]":
            items.append(self.consume("]"))

        while self.current() is not None and self.current() != "]":
            if self.current() == "[" and self.peek_next() == ":":
                posix_item = self.parse_posix_class()
                items.append(posix_item)
            else:
                if self.current() == "\\":
                    start_char = self.parse_escape()
                else:
                    start_char = self.consume()
                if self.current() == "-" and self.peek_next() not in ("]", None):
                    self.consume("-")
                    if self.current() == "\\":
                        end_char = self.parse_escape()
                    else:
                        end_char = self.consume()
                    items.append(ast.Range(start_char, end_char))
                else:
                    items.append(start_char)
        if self.current() != "]":
            self.error("Unterminated character class; missing ']'")
        self.consume("]")
        return ast.CharacterClass(negate, items)

    def parse_posix_class(self):
        self.consume("[")
        self.consume(":")
        name = ""
        while True:
            if self.current() is None:
                self.error("Unterminated POSIX character class; missing ':]'")
            if self.current() == ":" and self.peek_next() == "]":
                self.consume(":")
                self.consume("]")
                break
            else:
                name += self.consume()
        try:
            return ast.PosixClass(name)
        except ValueError:
            self.error(f"Unknown POSIX character class: {name}")

    def current(self):
        if self.pos < self.length:
            return self.regex[self.pos]
        return None

    def peek_next(self):
        if self.pos + 1 < self.length:
            return self.regex[self.pos + 1]
        return None

    def consume(self, ch=None) -> str:
        if self.pos >= self.length:
            self.error("Unexpected end of expression")
        cur = self.regex[self.pos]
        if ch is not None and cur != ch:
            self.error(f"Expected '{ch}' at position {self.pos}, but got '{cur}'")
        self.pos += 1
        return cur

    def error(self, msg):
        raise ParseError(msg + f" regex: {self.regex}")
