import z3

class Node:
    """Base class for all AST nodes."""
    pass

class Literal(Node):
    """Represents a literal character."""
    def __init__(self, char: str):
        self.char = char
    def __repr__(self):
        return f"Literal({self.char!r})"

class Dot(Node):
    """Represents the dot operator (matches any character)."""
    def __repr__(self):
        return "Dot()"

class Concat(Node):
    """Represents concatenation of expressions."""
    def __init__(self, nodes: list[Node]):
        self.nodes = nodes
    def __repr__(self):
        return f"Concat({self.nodes})"

class Quantifier(Node):
    """Represents a quantifier applied to an expression."""
    def __init__(self, node: Node, min_times: int, max_times: int | None):
        self.node = node
        self.min = min_times
        self.max = max_times  # None means no upper bound
    def __repr__(self):
        return f"Quantifier({self.node}, {self.min}, {self.max})"

class Range(Node):
    """Represents a range of characters (e.g. a-z)."""
    def __init__(self, start: str, end: str):
        self.start = start
        self.end = end
    def __repr__(self):
        return f"Range({self.start!r}-{self.end!r})"
    
class PosixClass(Node):
    """Represents a POSIX character class (e.g. [:upper:])."""
    def __init__(self, name: str):
        self.name = name
    def __repr__(self):
        return f"PosixClass({self.name!r})"

class CharacterClass(Node):
    """Represents a character class (e.g. [a-z] or [^0-9])."""
    def __init__(self, negate: bool, items: list[Literal | Range | PosixClass]):
        self.negate = negate
        self.items = items
    def __repr__(self):
        return f"CharacterClass(negate={self.negate}, items={self.items})"

class Intersection(Node):
    """Represents the intersection of two expressions using '&' (extended mode only)."""
    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"Intersection({self.left}, {self.right})"

class Complement(Node):
    """Represents the complement (prefix '!') of an expression (extended mode only)."""
    def __init__(self, node: Node):
        self.node = node
    def __repr__(self):
        return f"Complement({self.node})"

class Alternation(Node):
    """Represents alternation between two expressions."""
    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"Alternation({self.left}, {self.right})"

class StartAnchor(Node):
    """Represents a start-of-line anchor ('^')."""
    def __repr__(self):
        return "StartAnchor()"

class EndAnchor(Node):
    """Represents an end-of-line anchor ('$')."""
    def __repr__(self):
        return "EndAnchor()"


# === RegexParser Implementation (Extended and Basic Modes) ===

class RegexParser:
    def __init__(self, pattern, mode="extended"):
        """
        Initialize the parser.
        
        :param pattern: the regex pattern to parse.
        :param mode: "extended" for POSIX extended regex,
                     "basic" for POSIX basic regex.
        """
        self.pattern = pattern
        self.pos = 0
        self.length = len(pattern)
        if mode not in ("extended", "basic"):
            raise ValueError("Mode must be either 'extended' or 'basic'")
        self.mode = mode

    def current(self):
        """Return the current character or None if at end of pattern."""
        if self.pos < self.length:
            return self.pattern[self.pos]
        return None

    def peek_next(self):
        """Return the next character without consuming it."""
        if self.pos + 1 < self.length:
            return self.pattern[self.pos + 1]
        return None

    def consume(self, ch=None):
        """
        Consume the current character.
        If a character 'ch' is specified, verifies that the current character matches it.
        """
        if self.pos < self.length:
            cur = self.pattern[self.pos]
            if ch is not None and cur != ch:
                self.error(f"Expected '{ch}' at position {self.pos}, but got '{cur}'")
            self.pos += 1
            return cur
        return None

    def error(self, msg):
        """Raise a parsing error with the given message."""
        raise ValueError(msg)

    def parse(self):
        """Parse the entire pattern and return the AST."""
        node = self.parse_union_expr()  # lowest precedence: alternation
        if self.pos != self.length:
            self.error(f"Extra characters found at position {self.pos}: {self.pattern[self.pos:]}")
        return node

    # --- Alternation (Union) ---
    def parse_union_expr(self):
        """
        Parse an expression with the alternation operator.
        In extended mode, alternation is recognized with an unescaped '|'.
        In basic mode, alternation must be written as "\|".
        """
        node = self.parse_intersect_expr()
        if self.mode == "extended":
            while self.current() == '|':
                self.consume('|')
                right = self.parse_intersect_expr()
                node = Alternation(node, right)
        else:  # basic mode: check for escaped alternation "\|"
            while self.current() == '\\' and self.peek_next() == '|':
                self.consume('\\')
                self.consume('|')
                right = self.parse_intersect_expr()
                node = Alternation(node, right)
        return node

    # --- Intersection ---
    def parse_intersect_expr(self):
        """
        Parse an expression with the intersection operator '&'.
        (Supported only in extended mode; in basic mode '&' is treated as literal.)
        """
        if self.mode == "extended":
            node = self.parse_concat_expr()
            while self.current() == '&':
                self.consume('&')
                right = self.parse_concat_expr()
                node = Intersection(node, right)
            return node
        else:
            return self.parse_concat_expr()

    # --- Concatenation ---
    def parse_concat_expr(self):
        """
        Parse an implicit concatenation of expressions.
        In extended mode, terminators are: ')', '|' and '&'.
        In basic mode, if the next two characters form an escaped alternation "\|",
        concatenation is terminated so that the union parser can handle it.
        """
        nodes = []
        while self.pos < self.length and not self._concat_terminator():
            node = self.parse_repetition_expr()
            if node is not None:
                nodes.append(node)
            else:
                break
        if not nodes:
            # Return an empty literal if no expression is found.
            return Literal("")
        if len(nodes) == 1:
            return nodes[0]
        return Concat(nodes)
    
    def _concat_terminator(self):
        """
        Returns True if the current token should terminate concatenation.
        In extended mode, these are ')', '|' and '&'.
        In basic mode, if the next two characters form an escaped alternation ("\|")
        then concatenation terminates.
        """
        cur = self.current()
        if self.mode == "extended":
            return cur in [')', '|', '&']
        else:
            if cur == '\\' and self.peek_next() == '|':
                return True
            return False

    # --- Repetition (Quantifiers) ---
    def parse_repetition_expr(self):
        """
        Parse an expression possibly followed by quantifiers.
        In extended mode, quantifiers *, +, ?, and {…} are active.
        In basic mode, only '*' is active unescaped.
        In basic mode, '+', '?' and '{…}' must be written as "\+", "\?" and "\{…\}".
        """
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
                    # Unescaped '{' in extended mode introduces a braced quantifier.
                    min_val, max_val = self.parse_braced_quantifier(escaped=False)
                    node = Quantifier(node, min_val, max_val)
                else:
                    break
            return node
        else:  # basic mode
            while True:
                curr = self.current()
                if curr == '*':
                    self.consume('*')
                    node = Quantifier(node, 0, None)
                # In basic mode, '+', '?' and '{' are meta only if escaped.
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
        """
        Parse a braced quantifier.
        In extended mode, the syntax is {m} or {m,n} (with numbers).
        In basic mode (escaped=True) the opening must be "\{" and the closing as "\}".
        """
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
            # In basic mode, the closing brace must be escaped as "\}"
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

    # --- Unary Expressions ---
    def parse_unary_expr(self):
        """
        Parse an expression with a unary prefix operator.
        In extended mode, the complement operator '!' is supported.
        In basic mode, '!' is treated as literal.
        """
        if self.mode == "extended" and self.current() == '!':
            self.consume('!')
            node = self.parse_unary_expr()
            return Complement(node)
        else:
            return self.parse_primary()

    # --- Primary Expressions ---
    def parse_primary(self):
        """
        Parse a primary expression which can be:
          - A parenthesized expression (grouping)
          - A character class
          - The dot operator '.'
          - An anchor: '^' or '$'
          - An escape sequence (which may represent a literal)
          - A literal character
          
        In extended mode, grouping is recognized with ( … ).
        In basic mode, grouping must be written as "\(" … "\)".
        """
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
        else:  # basic mode
            # Grouping: must be written as "\(" ... "\)"
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
        """
        Helper method for basic mode grouping.
        This method consumes characters until it finds the matching escaped "\)".
        It supports nested groups.
        Returns the AST parsed from the group content.
        """
        content = ""
        group_level = 1
        while self.pos < self.length:
            # Check for nested group start: "\("
            if self.current() == '\\' and self.peek_next() == '(':
                group_level += 1
                content += self.consume()  # add '\' 
                content += self.consume()  # add '('
            # Check for group end: "\)"
            elif self.current() == '\\' and self.peek_next() == ')':
                group_level -= 1
                self.consume()  # consume '\' 
                self.consume()  # consume ')'
                if group_level == 0:
                    break
                else:
                    content += "\\)"
            else:
                content += self.consume()
        if group_level != 0:
            self.error("Missing closing escaped ')' for group in basic mode")
        # Parse the content as a basic-mode regex.
        subparser = RegexParser(content, mode="basic")
        return subparser.parse()

    # --- Escapes ---
    def parse_escape(self):
        """
        Parse an escape sequence.
        Supports common escapes such as \n, \t, \r and ensures that meta characters
        (like +, {, }, |, &, !, *, ?, ^, $, etc.) are returned literally.
        The same mapping is used in both modes.
        """
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

    # --- Character Classes ---
    def parse_character_class(self):
        """
        Parse a character class expression.
        Supports:
          - Negation with '^' immediately after '['
          - Ranges (e.g. a-z)
          - POSIX character classes (e.g. [:upper:]) inside the class
        """
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
        """
        Parse a POSIX character class of the form [:name:].
        Allowed names: upper, lower, alpha, digit, xdigit, alnum, punct,
                       blank, space, cntrl, graph, print.
        """
        self.consume('[')  # consume '['
        self.consume(':')  # consume ':'
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


# === AST to Extended Regex Translator ===

def get_prec(node):
    """
    Return an integer indicating the precedence of the node.
    Lower numbers indicate looser binding.
      Alternation:      1
      Intersection:     2
      Concatenation:    3
      Complement:       4
      Quantifier:       5
      Atoms:            6
    """
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
    """
    Escape a literal character if it is a meta character in extended regex.
    Meta characters are: ^ $ . * + ? { } [ ] ( ) | & ! \
    """
    meta = "^$.*+?{}[]()|&!\\"
    if ch in meta:
        return "\\" + ch
    return ch

def escape_char_class(ch):
    """
    Escape a character for inclusion inside a character class.
    In a character class, typically ']' and '\' must be escaped.
    """
    if ch in "\\]":
        return "\\" + ch
    return ch

def to_regex(node, parent_prec=0):
    """Recursively convert the AST node to an extended regex string."""
    my_prec = get_prec(node)
    if isinstance(node, Literal):
        s = escape_literal(node.char)
    elif isinstance(node, Dot):
        s = "."
    elif isinstance(node, Concat):
        # For concatenation, join the children.
        s = "".join(to_regex(child, get_prec(node)) for child in node.nodes)
    elif isinstance(node, Quantifier):
        base = to_regex(node.node, get_prec(node))
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
                s += to_regex(item)
        s += "]"
    elif isinstance(node, Intersection):
        left = to_regex(node.left, get_prec(node))
        right = to_regex(node.right, get_prec(node)+1)
        s = left + "&" + right
    elif isinstance(node, Complement):
        s = "!" + to_regex(node.node, get_prec(node))
    elif isinstance(node, Alternation):
        left = to_regex(node.left, get_prec(node))
        right = to_regex(node.right, get_prec(node)+1)
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
    

def to_z3(node):
    any_char = z3.Range(chr(0), chr(127))
    if isinstance(node, Literal):
        return z3.Re(node.char)
    elif isinstance(node, Dot):
        return any_char
    elif isinstance(node, Concat):
        return z3.Concat([to_z3(child) for child in node.nodes])
    elif isinstance(node, Quantifier):
        base = to_z3(node.node)
        if node.min == 0 and node.max == 1:
            return z3.Option(base)
        elif node.max is not None:
            return z3.Loop(base, node.min, node.max)
        elif node.min == 0: # 0 or more
            return z3.Star(base)
        elif node.min == 1: # 1 or more
            return z3.Plus(base)
        else: # min or more
            return z3.Concat(z3.Loop(base, node.min, node.min), z3.Star(base))
    elif isinstance(node, CharacterClass):
        items = [to_z3(item) for item in node.items]
        if node.negate:
            return z3.Intersect(any_char, z3.Complement(z3.Union(items)))
        return z3.Union(items)
    elif isinstance(node, Range):
        return z3.Range(node.start, node.end)
    elif isinstance(node, Intersection):
        return z3.Intersect(to_z3(node.left), to_z3(node.right))
    elif isinstance(node, Complement):
        return z3.Intersect(z3.Star(any_char), z3.Complement(to_z3(node.node)))
    elif isinstance(node, Alternation):
        return z3.Union(to_z3(node.left), to_z3(node.right))
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
        pass
    elif isinstance(node, EndAnchor):
        pass
    else:
        raise ValueError(f"Unknown node type: {node}")


def ast_to_extended_regex(ast):
    """Convert an AST to an extended regex string."""
    return to_regex(ast, 0)


# === Main Usage Example ===

if __name__ == "__main__":
    # Example:
    # Enter a regex in extended mode (which supports & and !), for example:
    #     ^a\+b | c\{2,3\} & ![[:digit:]-z]$
    #
    # Then the AST is generated and then translated back to an extended regex.
    pattern = input("Enter regex: ")
    mode = input("Enter mode ('extended' or 'basic'): ").strip().lower()
    parser = RegexParser(pattern, mode=mode)
    try:
        ast = parser.parse()
        print("Generated AST:")
        print(ast)
        # Now translate AST to an extended regex string.
        ext_regex = ast_to_extended_regex(ast)
        print("\nTranslated Extended Regex:")
        print(ext_regex)

        # Translate AST to Z3 regex
        z3_regex = to_z3(ast)
        print("\nZ3 Regex:")
        print(z3_regex)
    except ValueError as e:
        print("Parsing error:", e)
