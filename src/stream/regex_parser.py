import z3

class Node:
    pass

class Literal(Node):
    def __init__(self, char: str):
        self.char = char
    def __repr__(self):
        return f"Literal({self.char!r})"

class Dot(Node):
    def __repr__(self):
        return "Dot()"

class Concat(Node):
    def __init__(self, nodes: list[Node]):
        self.nodes = nodes
    def __repr__(self):
        return f"Concat({self.nodes})"

class Quantifier(Node):
    def __init__(self, node: Node, min_times: int, max_times: int | None):
        self.node = node
        self.min = min_times
        self.max = max_times
    def __repr__(self):
        return f"Quantifier({self.node}, {self.min}, {self.max})"

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

class Alternation(Node):
    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"Alternation({self.left}, {self.right})"

class StartAnchor(Node):
    def __repr__(self):
        return "StartAnchor()"

class EndAnchor(Node):
    def __repr__(self):
        return "EndAnchor()"

class RegexParser:
    def __init__(self, pattern, mode="extended"):
        self.pattern = pattern
        self.pos = 0
        self.length = len(pattern)
        if mode not in ("extended", "basic"):
            raise ValueError("Mode must be either 'extended' or 'basic'")
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
        if self.mode == "extended":
            while self.current() == '|':
                self.consume('|')
                right = self.parse_intersect_expr()
                node = Alternation(node, right)
        else:
            while self.current() == '\\' and self.peek_next() == '|':
                self.consume('\\')
                self.consume('|')
                right = self.parse_intersect_expr()
                node = Alternation(node, right)
        return node

    def parse_intersect_expr(self):
        if self.mode == "extended":
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
        return Concat(nodes)
    
    def _concat_terminator(self):
        cur = self.current()
        if self.mode == "extended":
            return cur in [')', '|', '&']
        else:
            if cur == '\\' and self.peek_next() == '|':
                return True
            return False

    def parse_repetition_expr(self):
        node = self.parse_unary_expr()
        if self.mode == "extended":
            while True:
                curr = self.current()
                if curr is not None and curr in ('*', '+', '?'):
                    op = self.consume()
                    if op == '*':
                        node = Quantifier(node, 0, None)
                    elif op == '+':
                        node = Quantifier(node, 1, None)
                    elif op == '?':
                        node = Quantifier(node, 0, 1)
                elif curr == '{':
                    min_val, max_val = self.parse_braced_quantifier(escaped=False)
                    node = Quantifier(node, min_val, max_val)
                else:
                    break
            return node
        else:
            while True:
                curr = self.current()
                if curr == '*':
                    self.consume('*')
                    node = Quantifier(node, 0, None)
                elif curr == '\\' and self.peek_next() in ['+', '?', '{']:
                    self.consume('\\')
                    op = self.consume()
                    if op == '+':
                        node = Quantifier(node, 1, None)
                    elif op == '?':
                        node = Quantifier(node, 0, 1)
                    elif op == '{':
                        min_val, max_val = self.parse_braced_quantifier(escaped=True)
                        node = Quantifier(node, min_val, max_val)
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
        if self.mode == "extended" and self.current() == '!':
            self.consume('!')
            if self.pos >= self.length or self.current() in [')', '|', '&']:
                return Complement(Literal(""))
            else:
                node = self.parse_unary_expr()
                return Complement(node)
        else:
            return self.parse_primary()

    def parse_primary(self):
        curr = self.current()
        if curr is None:
            self.error("Unexpected end of expression")
        
        if self.mode == "extended":
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
            '+': '+',
            '{': '{',
            '}': '}',
            '|': '|',
            '&': '&',
            '!': '!',
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
    if isinstance(node, Alternation):
        return 1
    elif isinstance(node, Intersection):
        return 2
    elif isinstance(node, Concat):
        return 3
    elif isinstance(node, Complement):
        return 4
    elif isinstance(node, Quantifier):
        return 5
    else:
        return 6

def escape_literal(ch):
    meta = "^$.*+?{}[]()|&!\\"
    if ch in meta:
        return "\\" + ch
    return ch

def escape_char_class(ch):
    if ch in "\\]":
        return "\\" + ch
    return ch

def _ast_to_regex(node, parent_prec=0):
    my_prec = get_prec(node)
    if isinstance(node, Literal):
        s = escape_literal(node.char)
    elif isinstance(node, Dot):
        s = "."
    elif isinstance(node, Concat):
        s = "".join(_ast_to_regex(child, get_prec(node)) for child in node.nodes)
    elif isinstance(node, Quantifier):
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
        s = "!" + _ast_to_regex(node.node, get_prec(node))
    elif isinstance(node, Alternation):
        left = _ast_to_regex(node.left, get_prec(node))
        right = _ast_to_regex(node.right, get_prec(node)+1)
        s = left + "|" + right
    elif isinstance(node, StartAnchor):
        s = "^"
    elif isinstance(node, EndAnchor):
        s = "$"
    else:
        s = ""
    if my_prec < parent_prec:
        return "(" + s + ")"
    else:
        return s
    

def ast_to_z3(node):
    # any_char = z3.Range(chr(0), chr(127))
    any_char = z3.Range(chr(0), chr(126))
    if isinstance(node, Literal):
        return z3.Re(node.char)
    elif isinstance(node, Dot):
        return any_char
    elif isinstance(node, Concat):
        children = [ast_to_z3(child) for child in node.nodes]
        children = [child for child in children if child != None]
        if len(children) == 0:
            return z3.Re("")
        if len(children) == 1:
            return children[0]
        return z3.Concat(children)
    elif isinstance(node, Quantifier):
        base = ast_to_z3(node.node)
        if node.min == 0 and node.max == 1:
            return z3.Option(base)
        elif node.max is not None:
            return z3.Loop(base, node.min, node.max)
        elif node.min == 0:
            return z3.Star(base)
        elif node.min == 1:
            return z3.Plus(base)
        else:
            return z3.Concat(z3.Loop(base, node.min, node.min), z3.Star(base))
    elif isinstance(node, CharacterClass):
        items = [ast_to_z3(item) for item in node.items]
        if node.negate:
            return z3.Intersect(any_char, z3.Complement(z3.Union(items)))
        return z3.Union(items)
    elif isinstance(node, Range):
        return z3.Range(node.start, node.end)
    elif isinstance(node, Intersection):
        return z3.Intersect(ast_to_z3(node.left), ast_to_z3(node.right))
    elif isinstance(node, Complement):
        return z3.Intersect(z3.Star(any_char), z3.Complement(ast_to_z3(node.node)))
    elif isinstance(node, Alternation):
        return z3.Union(ast_to_z3(node.left), ast_to_z3(node.right))
    elif isinstance(node, PosixClass):
        name = node.name
        if name == "upper":
            return z3.Range("A", "Z")
        elif name == "lower":
            return z3.Range("a", "z")
        elif name == "alpha":
            return z3.Union(z3.Range("A", "Z"), z3.Range("a", "z"))
        elif name == "digit":
            return z3.Range("0", "9")
        elif name == "xdigit":
            return z3.Union(z3.Range("0", "9"), z3.Range("A", "F"), z3.Range("a", "f"))
        elif name == "alnum":
            return z3.Union(z3.Range("A", "Z"), z3.Range("a", "z"), z3.Range("0", "9"))
        elif name == "punct":
            return z3.Union(
                z3.Range("!", "/"),
                z3.Range(":", "@"),
                z3.Range("[", "`"),
                z3.Range("{", "~")
            )
        elif name == "blank":
            return z3.Union(z3.Re(" "), z3.Re("\t"))
        elif name == "space":
            return z3.Union(
                z3.Re(" "),
                z3.Re("\t"),
                z3.Re("\n"),
                z3.Re("\r"),
                z3.Re("\v"),
                z3.Re("\f")
            )
        elif name == "cntrl":
            return z3.Union(z3.Range(chr(0), chr(31)), z3.Range(chr(127), chr(127)))
        elif name == "graph":
            return z3.Range(chr(33), chr(126))
        elif name == "print":
            return z3.Range(chr(32), chr(126))
        else:
            raise ValueError(f"Unknown POSIX character class: {name}")
    elif isinstance(node, StartAnchor):
        return z3.Re("")
    elif isinstance(node, EndAnchor):
        return z3.Re("")
    else:
        raise ValueError(f"Unknown node type: {node}")

def ast_to_regex(ast):
    return _ast_to_regex(ast, 0)

if __name__ == "__main__":
    pattern = input("Enter regex: ")
    mode = "extended"
    parser = RegexParser(pattern, mode=mode)
    try:
        ast = parser.parse()
        print("Generated AST:")
        print(ast)
        ext_regex = ast_to_regex(ast)
        print("\nTranslated Extended Regex:")
        print(ext_regex)
        z3_regex = ast_to_z3(ast)
        print("\nZ3 Regex:")
        print(z3_regex)
    except ValueError as e:
        print("Parsing error:", e)
