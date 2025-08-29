import re
from typing import List, Optional, Union, Dict, Any
from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    # Literals
    NUMBER = "NUMBER"
    STRING = "STRING"
    REGEX = "REGEX"
    FIELD = "FIELD"  # $1, $2, $0, $NF
    
    # Identifiers and keywords
    IDENTIFIER = "IDENTIFIER"
    BEGIN = "BEGIN"
    END = "END"
    IF = "IF"
    ELSE = "ELSE"
    FOR = "FOR"
    WHILE = "WHILE"
    PRINT = "PRINT"
    PRINTF = "PRINTF"
    IN = "IN"
    
    # Operators
    ASSIGN = "="
    PLUS_ASSIGN = "+="
    MINUS_ASSIGN = "-="
    MULT_ASSIGN = "*="
    DIV_ASSIGN = "/="
    MOD_ASSIGN = "%="
    INCREMENT = "++"
    DECREMENT = "--"
    
    PLUS = "+"
    MINUS = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULO = "%"
    
    EQ = "=="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    MATCH = "~"
    NOT_MATCH = "!~"
    
    AND = "&&"
    OR = "||"
    NOT = "!"
    
    # Punctuation
    LBRACE = "{"
    RBRACE = "}"
    LPAREN = "("
    RPAREN = ")"
    LBRACKET = "["
    RBRACKET = "]"
    SEMICOLON = ";"
    COMMA = ","
    QUESTION = "?"
    COLON = ":"
    
    # Special
    NEWLINE = "NEWLINE"
    EOF = "EOF"
    WHITESPACE = "WHITESPACE"


@dataclass
class Token:
    type: TokenType
    value: str
    line: int = 1
    column: int = 1


@dataclass
class AwkNode:
    """Base class for all AWK AST nodes"""
    pass


@dataclass
class AwkProgram(AwkNode):
    """Root node representing an entire AWK program"""
    rules: List['AwkRule']


@dataclass
class AwkRule(AwkNode):
    """A pattern-action pair: pattern { action }"""
    pattern: Optional['AwkPattern']
    action: 'AwkAction'


@dataclass
class AwkPattern(AwkNode):
    """Base class for patterns"""
    pass


@dataclass
class RegexPattern(AwkPattern):
    """Regex pattern: /regex/"""
    regex: str


@dataclass
class ExpressionPattern(AwkPattern):
    """Expression pattern: NR > 1, ($9 ~ /404/)"""
    expression: 'AwkExpression'


@dataclass
class BeginPattern(AwkPattern):
    """BEGIN pattern"""
    pass


@dataclass
class EndPattern(AwkPattern):
    """END pattern"""
    pass


@dataclass
class AwkAction(AwkNode):
    """Action block containing statements"""
    statements: List['AwkStatement']


@dataclass
class AwkStatement(AwkNode):
    """Base class for statements"""
    pass


@dataclass
class PrintStatement(AwkStatement):
    """print statement"""
    expressions: List['AwkExpression']


@dataclass
class PrintfStatement(AwkStatement):
    """printf statement"""
    format_string: 'AwkExpression'
    arguments: List['AwkExpression']


@dataclass
class AssignmentStatement(AwkStatement):
    """Assignment statement: var = expr, var += expr, etc."""
    target: 'AwkExpression'
    operator: str  # =, +=, -=, etc.
    value: 'AwkExpression'


@dataclass
class IncrementStatement(AwkStatement):
    """Increment/decrement statement: var++, ++var, var--, --var"""
    variable: 'AwkExpression'
    operator: str  # ++, --
    prefix: bool  # True for ++var, False for var++


@dataclass
class IfStatement(AwkStatement):
    """if statement"""
    condition: 'AwkExpression'
    then_action: AwkAction
    else_action: Optional[AwkAction] = None


@dataclass
class ForStatement(AwkStatement):
    """for statement"""
    variable: str
    iterable: 'AwkExpression'
    action: AwkAction


@dataclass
class AwkExpression(AwkNode):
    """Base class for expressions"""
    pass


@dataclass
class BinaryOperation(AwkExpression):
    """Binary operation: left op right"""
    left: AwkExpression
    operator: str
    right: AwkExpression


@dataclass
class UnaryOperation(AwkExpression):
    """Unary operation: op operand"""
    operator: str
    operand: AwkExpression


@dataclass
class FieldReference(AwkExpression):
    """Field reference: $1, $2, $0, $NF"""
    index: AwkExpression


@dataclass
class Variable(AwkExpression):
    """Variable reference"""
    name: str


@dataclass
class ArrayAccess(AwkExpression):
    """Array access: array[index]"""
    array: AwkExpression
    index: AwkExpression


@dataclass
class StringLiteral(AwkExpression):
    """String literal"""
    value: str


@dataclass
class NumberLiteral(AwkExpression):
    """Number literal"""
    value: Union[int, float]


@dataclass
class RegexLiteral(AwkExpression):
    """Regex literal: /pattern/"""
    pattern: str


@dataclass
class FunctionCall(AwkExpression):
    """Function call: func(arg1, arg2, ...)"""
    function_name: str
    arguments: List[AwkExpression]


@dataclass
class ConditionalExpression(AwkExpression):
    """Ternary conditional: condition ? true_expr : false_expr"""
    condition: AwkExpression
    true_expr: AwkExpression
    false_expr: AwkExpression


class AwkLexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []
    
    def tokenize(self) -> List[Token]:
        """Tokenize the AWK program text"""
        while self.pos < len(self.text):
            self._skip_whitespace()
            if self.pos >= len(self.text):
                break
                
            if self._match_regex():
                continue
            elif self._match_string():
                continue
            elif self._match_field():
                continue
            elif self._match_number():
                continue
            elif self._match_operator():
                continue
            elif self._match_keyword():
                continue
            elif self._match_identifier():
                continue
            elif self._match_punctuation():
                continue
            else:
                # Skip unknown character
                self._advance()
        
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens
    
    def _advance(self) -> str:
        """Advance position and return current character"""
        if self.pos >= len(self.text):
            return ""
        char = self.text[self.pos]
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char
    
    def _peek(self, offset: int = 0) -> str:
        """Peek at character at current position + offset"""
        pos = self.pos + offset
        if pos >= len(self.text):
            return ""
        return self.text[pos]
    
    def _skip_whitespace(self):
        """Skip whitespace characters"""
        while self.pos < len(self.text) and self.text[self.pos] in ' \t':
            self._advance()
    
    def _match_regex(self) -> bool:
        """Match regex literal: /pattern/"""
        if self._peek() != '/':
            return False
        
        # Check if this '/' should be treated as division instead of regex
        if len(self.tokens) > 0:
            last_token = self.tokens[-1]
            # If previous token suggests this could be division, don't treat as regex
            if last_token.type in [TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.FIELD,
                                   TokenType.RBRACKET, TokenType.RPAREN]:
                return False
        
        start_pos = self.pos
        start_col = self.column
        self._advance()  # Skip '/'
        
        pattern = ""
        while self.pos < len(self.text) and self._peek() != '/':
            if self._peek() == '\\':
                self._advance()  # Skip backslash
                if self.pos < len(self.text):
                    pattern += self._advance()  # Add escaped character
            else:
                pattern += self._advance()
        
        if self.pos < len(self.text) and self._peek() == '/':
            self._advance()  # Skip closing '/'
            self.tokens.append(Token(TokenType.REGEX, pattern, self.line, start_col))
            return True
        else:
            # Not a valid regex, backtrack
            self.pos = start_pos
            self.column = start_col
            return False
    
    def _match_string(self) -> bool:
        """Match string literal"""
        if self._peek() not in '"\'':
            return False
        
        quote = self._peek()
        start_col = self.column
        self._advance()  # Skip opening quote
        
        value = ""
        while self.pos < len(self.text) and self._peek() != quote:
            if self._peek() == '\\':
                self._advance()  # Skip backslash
                if self.pos < len(self.text):
                    escaped = self._advance()
                    # Handle common escape sequences
                    if escaped == 'n':
                        value += '\n'
                    elif escaped == 't':
                        value += '\t'
                    elif escaped == 'r':
                        value += '\r'
                    elif escaped == '\\':
                        value += '\\'
                    elif escaped == quote:
                        value += quote
                    else:
                        value += escaped
            else:
                value += self._advance()
        
        if self.pos < len(self.text) and self._peek() == quote:
            self._advance()  # Skip closing quote
            self.tokens.append(Token(TokenType.STRING, value, self.line, start_col))
            return True
        
        return False
    
    def _match_field(self) -> bool:
        """Match field reference: $1, $2, $NF, etc."""
        if self._peek() != '$':
            return False
        
        start_col = self.column
        self._advance()  # Skip '$'
        
        # Get the field expression (number or variable)
        field_expr = ""
        if self._peek().isdigit():
            while self.pos < len(self.text) and self._peek().isdigit():
                field_expr += self._advance()
        elif self._peek().isalpha() or self._peek() == '_':
            while (self.pos < len(self.text) and 
                   (self._peek().isalnum() or self._peek() == '_')):
                field_expr += self._advance()
        
        if field_expr:
            self.tokens.append(Token(TokenType.FIELD, field_expr, self.line, start_col))
            return True
        
        return False
    
    def _match_number(self) -> bool:
        """Match number literal"""
        if not self._peek().isdigit():
            return False
        
        start_col = self.column
        value = ""
        
        # Integer part
        while self.pos < len(self.text) and self._peek().isdigit():
            value += self._advance()
        
        # Decimal part
        if self.pos < len(self.text) and self._peek() == '.':
            value += self._advance()
            while self.pos < len(self.text) and self._peek().isdigit():
                value += self._advance()
        
        self.tokens.append(Token(TokenType.NUMBER, value, self.line, start_col))
        return True
    
    def _match_operator(self) -> bool:
        """Match operators"""
        operators = {
            '++': TokenType.INCREMENT,
            '--': TokenType.DECREMENT,
            '+=': TokenType.PLUS_ASSIGN,
            '-=': TokenType.MINUS_ASSIGN,
            '*=': TokenType.MULT_ASSIGN,
            '/=': TokenType.DIV_ASSIGN,
            '%=': TokenType.MOD_ASSIGN,
            '==': TokenType.EQ,
            '!=': TokenType.NE,
            '<=': TokenType.LE,
            '>=': TokenType.GE,
            '!~': TokenType.NOT_MATCH,
            '&&': TokenType.AND,
            '||': TokenType.OR,
            '~': TokenType.MATCH,
            '=': TokenType.ASSIGN,
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.MULTIPLY,
            '/': TokenType.DIVIDE,
            '%': TokenType.MODULO,
            '<': TokenType.LT,
            '>': TokenType.GT,
            '!': TokenType.NOT,
        }
        
        # Try two-character operators first
        two_char = self.text[self.pos:self.pos+2] if self.pos + 1 < len(self.text) else ""
        if two_char in operators:
            start_col = self.column
            self._advance()
            self._advance()
            self.tokens.append(Token(operators[two_char], two_char, self.line, start_col))
            return True
        
        # Try one-character operators
        one_char = self._peek()
        if one_char in operators:
            start_col = self.column
            self._advance()
            self.tokens.append(Token(operators[one_char], one_char, self.line, start_col))
            return True
        
        return False
    
    def _match_keyword(self) -> bool:
        """Match keywords"""
        keywords = {
            'BEGIN': TokenType.BEGIN,
            'END': TokenType.END,
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'for': TokenType.FOR,
            'while': TokenType.WHILE,
            'print': TokenType.PRINT,
            'printf': TokenType.PRINTF,
            'in': TokenType.IN,
        }
        
        start_pos = self.pos
        start_col = self.column
        
        # Read identifier
        identifier = ""
        if self._peek().isalpha() or self._peek() == '_':
            while (self.pos < len(self.text) and 
                   (self._peek().isalnum() or self._peek() == '_')):
                identifier += self._advance()
        
        if identifier in keywords:
            self.tokens.append(Token(keywords[identifier], identifier, self.line, start_col))
            return True
        else:
            # Not a keyword, backtrack
            self.pos = start_pos
            self.column = start_col
            return False
    
    def _match_identifier(self) -> bool:
        """Match identifier"""
        if not (self._peek().isalpha() or self._peek() == '_'):
            return False
        
        start_col = self.column
        identifier = ""
        
        while (self.pos < len(self.text) and 
               (self._peek().isalnum() or self._peek() == '_')):
            identifier += self._advance()
        
        self.tokens.append(Token(TokenType.IDENTIFIER, identifier, self.line, start_col))
        return True
    
    def _match_punctuation(self) -> bool:
        """Match punctuation"""
        punctuation = {
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '[': TokenType.LBRACKET,
            ']': TokenType.RBRACKET,
            ';': TokenType.SEMICOLON,
            ',': TokenType.COMMA,
            '?': TokenType.QUESTION,
            ':': TokenType.COLON,
            '\n': TokenType.NEWLINE,
        }
        
        char = self._peek()
        if char in punctuation:
            start_col = self.column
            self._advance()
            if char != '\n':  # Skip newlines for now
                self.tokens.append(Token(punctuation[char], char, self.line, start_col))
            return True
        
        return False


class AwkParser:
    def __init__(self, tokens: List[Token]):
        self.tokens = [t for t in tokens if t.type != TokenType.WHITESPACE]  # Filter whitespace
        self.pos = 0
        self.current_token = self.tokens[0] if self.tokens else Token(TokenType.EOF, "")
    
    def parse(self) -> AwkProgram:
        """Parse tokens into an AWK program AST"""
        rules = []
        
        while self.current_token.type != TokenType.EOF:
            rule = self._parse_rule()
            if rule:
                rules.append(rule)
            else:
                break
        
        return AwkProgram(rules)
    
    def _advance(self):
        """Move to next token"""
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
            self.current_token = self.tokens[self.pos]
    
    def _peek(self, offset: int = 1) -> Token:
        """Peek at next token"""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return Token(TokenType.EOF, "")
    
    def _expect(self, token_type: TokenType) -> Token:
        """Expect a specific token type"""
        if self.current_token.type == token_type:
            token = self.current_token
            self._advance()
            return token
        else:
            raise SyntaxError(f"Expected {token_type}, got {self.current_token.type}")
    
    def _parse_rule(self) -> Optional[AwkRule]:
        """Parse a pattern-action rule"""
        pattern = None
        
        if self.current_token.type == TokenType.BEGIN:
            pattern = BeginPattern()
            self._advance()
        elif self.current_token.type == TokenType.END:
            pattern = EndPattern()
            self._advance()
        elif self.current_token.type == TokenType.REGEX:
            pattern = RegexPattern(self.current_token.value)
            self._advance()
        elif self.current_token.type == TokenType.LBRACE:
            # No pattern, just action
            pass
        else:
            expr = self._parse_expression()
            if expr:
                pattern = ExpressionPattern(expr)
        
        if self.current_token.type == TokenType.LBRACE:
            action = self._parse_action()
            return AwkRule(pattern, action)
        else:
            if pattern:
                # Create an empty action
                return AwkRule(pattern, AwkAction([]))
        
        return None
    
    def _parse_action(self) -> AwkAction:
        """Parse action block"""
        self._expect(TokenType.LBRACE)
        statements = []
        
        while self.current_token.type != TokenType.RBRACE and self.current_token.type != TokenType.EOF:
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
            
            # skip semicolons and newlines
            while self.current_token.type in [TokenType.SEMICOLON, TokenType.NEWLINE]:
                self._advance()
        
        self._expect(TokenType.RBRACE)
        return AwkAction(statements)
    
    def _parse_statement(self) -> Optional[AwkStatement]:
        """Parse a statement"""
        if self.current_token.type == TokenType.PRINT:
            return self._parse_print_statement()
        elif self.current_token.type == TokenType.PRINTF:
            return self._parse_printf_statement()
        elif self.current_token.type == TokenType.IF:
            return self._parse_if_statement()
        elif self.current_token.type == TokenType.FOR:
            return self._parse_for_statement()
        elif self.current_token.type in [TokenType.INCREMENT, TokenType.DECREMENT]:
            return self._parse_increment_statement()
        else:
            return self._parse_assignment_or_expression()
    
    def _parse_print_statement(self) -> PrintStatement:
        """Parse print statement"""
        self._expect(TokenType.PRINT)
        expressions = []
        
        if self.current_token.type not in [TokenType.SEMICOLON, TokenType.RBRACE, TokenType.NEWLINE]:
            expressions.append(self._parse_expression())
            
            while self.current_token.type == TokenType.COMMA:
                self._advance()
                expressions.append(self._parse_expression())
            
            # Handle space-separated expressions (concatenation)
            while (self.current_token.type not in [TokenType.SEMICOLON, TokenType.RBRACE, TokenType.NEWLINE, TokenType.EOF] and
                   self.current_token.type not in [TokenType.COMMA]):
                expressions.append(self._parse_expression())
        
        return PrintStatement(expressions)
    
    def _parse_printf_statement(self) -> PrintfStatement:
        """Parse printf statement"""
        self._expect(TokenType.PRINTF)
        
        format_string = self._parse_expression()
        arguments = []
        
        while self.current_token.type == TokenType.COMMA:
            self._advance()
            arguments.append(self._parse_expression())
        
        return PrintfStatement(format_string, arguments)
    
    def _parse_if_statement(self) -> IfStatement:
        """Parse if statement"""
        self._expect(TokenType.IF)
        self._expect(TokenType.LPAREN)
        condition = self._parse_expression()
        self._expect(TokenType.RPAREN)
        
        if self.current_token.type == TokenType.LBRACE:
            # block
            then_action = self._parse_action()
        else:
            # single statement
            stmt = self._parse_statement()
            then_action = AwkAction([stmt] if stmt else [])
        
        else_action = None
        if self.current_token.type == TokenType.ELSE:
            self._advance()
            if self.current_token.type == TokenType.LBRACE:
                # block
                else_action = self._parse_action()
            else:
                # single statement
                stmt = self._parse_statement()
                else_action = AwkAction([stmt] if stmt else [])
        
        return IfStatement(condition, then_action, else_action)
    
    def _parse_for_statement(self) -> ForStatement:
        """Parse for statement"""
        self._expect(TokenType.FOR)
        self._expect(TokenType.LPAREN)
        
        var_name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.IN)
        iterable = self._parse_expression()
        
        self._expect(TokenType.RPAREN)
        
        # Action can be either a block or a single statement
        if self.current_token.type == TokenType.LBRACE:
            action = self._parse_action()
        else:
            # Single statement
            stmt = self._parse_statement()
            action = AwkAction([stmt] if stmt else [])
        
        return ForStatement(var_name, iterable, action)
    
    def _parse_increment_statement(self) -> IncrementStatement:
        """Parse increment/decrement statement"""
        if self.current_token.type in [TokenType.INCREMENT, TokenType.DECREMENT]:
            operator = self.current_token.value
            self._advance()
            variable = self._parse_primary()
            return IncrementStatement(variable, operator, True)
        else:
            variable = self._parse_primary()
            if self.current_token.type in [TokenType.INCREMENT, TokenType.DECREMENT]:
                operator = self.current_token.value
                self._advance()
                return IncrementStatement(variable, operator, False)
        
        return None
    
    def _parse_assignment_or_expression(self) -> Optional[AwkStatement]:
        """Parse assignment or expression statement"""
        expr = self._parse_expression()
        
        if self.current_token.type in [TokenType.ASSIGN, TokenType.PLUS_ASSIGN, 
                                       TokenType.MINUS_ASSIGN, TokenType.MULT_ASSIGN,
                                       TokenType.DIV_ASSIGN, TokenType.MOD_ASSIGN]:
            operator = self.current_token.value
            self._advance()
            value = self._parse_expression()
            return AssignmentStatement(expr, operator, value)
        
        if self.current_token.type in [TokenType.INCREMENT, TokenType.DECREMENT]:
            operator = self.current_token.value
            self._advance()
            return IncrementStatement(expr, operator, False)
        
        raise SyntaxError(f"Unknown assignment or expression statement: Unexpected token: {self.current_token.type} at position {self.pos}")
    
    def _parse_expression(self) -> AwkExpression:
        """Parse expression with precedence"""
        return self._parse_conditional()
    
    def _parse_conditional(self) -> AwkExpression:
        """Parse conditional expressions: condition ? true_expr : false_expr"""
        condition = self._parse_logical_or()
        
        if self.current_token.type == TokenType.QUESTION:
            self._advance()  # Skip '?'
            true_expr = self._parse_logical_or()
            self._expect(TokenType.COLON)
            false_expr = self._parse_conditional()  # Right associative
            return ConditionalExpression(condition, true_expr, false_expr)
        
        return condition
    
    def _parse_logical_or(self) -> AwkExpression:
        """Parse logical OR expressions"""
        left = self._parse_logical_and()
        
        while self.current_token.type == TokenType.OR:
            operator = self.current_token.value
            self._advance()
            right = self._parse_logical_and()
            left = BinaryOperation(left, operator, right)
        
        return left
    
    def _parse_logical_and(self) -> AwkExpression:
        """Parse logical AND expressions"""
        left = self._parse_regex_match()
        
        while self.current_token.type == TokenType.AND:
            operator = self.current_token.value
            self._advance()
            right = self._parse_regex_match()
            left = BinaryOperation(left, operator, right)
        
        return left
    
    def _parse_regex_match(self) -> AwkExpression:
        """Parse regex match expressions"""
        left = self._parse_relational()
        
        while self.current_token.type in [TokenType.MATCH, TokenType.NOT_MATCH]:
            operator = self.current_token.value
            self._advance()
            right = self._parse_relational()
            left = BinaryOperation(left, operator, right)
        
        return left
    
    def _parse_relational(self) -> AwkExpression:
        """Parse relational expressions"""
        left = self._parse_additive()
        
        while self.current_token.type in [TokenType.LT, TokenType.LE, TokenType.GT, 
                                          TokenType.GE, TokenType.EQ, TokenType.NE, TokenType.IN]:
            operator = self.current_token.value
            self._advance()
            right = self._parse_additive()
            left = BinaryOperation(left, operator, right)
        
        return left
    
    def _parse_additive(self) -> AwkExpression:
        """Parse additive expressions"""
        left = self._parse_multiplicative()
        
        while self.current_token.type in [TokenType.PLUS, TokenType.MINUS]:
            operator = self.current_token.value
            self._advance()
            right = self._parse_multiplicative()
            left = BinaryOperation(left, operator, right)
        
        return left
    
    def _parse_multiplicative(self) -> AwkExpression:
        """Parse multiplicative expressions"""
        left = self._parse_unary()
        
        while self.current_token.type in [TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO]:
            operator = self.current_token.value
            self._advance()
            right = self._parse_unary()
            left = BinaryOperation(left, operator, right)
        
        return left
    
    def _parse_unary(self) -> AwkExpression:
        """Parse unary expressions"""
        if self.current_token.type in [TokenType.NOT, TokenType.PLUS, TokenType.MINUS]:
            operator = self.current_token.value
            self._advance()
            operand = self._parse_unary()
            return UnaryOperation(operator, operand)
        elif self.current_token.type in [TokenType.INCREMENT, TokenType.DECREMENT]:
            operator = self.current_token.value
            self._advance()
            operand = self._parse_primary()
            return UnaryOperation(operator, operand)
        
        return self._parse_primary()
    
    def _parse_primary(self) -> AwkExpression:
        """Parse primary expressions"""
        if self.current_token.type == TokenType.NUMBER:
            value = self.current_token.value
            self._advance()
            if '.' in value:
                return NumberLiteral(float(value))
            else:
                return NumberLiteral(int(value))
        
        elif self.current_token.type == TokenType.STRING:
            value = self.current_token.value
            self._advance()
            return StringLiteral(value)
        
        elif self.current_token.type == TokenType.REGEX:
            pattern = self.current_token.value
            self._advance()
            return RegexLiteral(pattern)
        
        elif self.current_token.type == TokenType.FIELD:
            field_expr = self.current_token.value
            self._advance()
            
            # Convert field string to expression, distinguish between $1 and $NF
            if field_expr.isdigit():
                index = NumberLiteral(int(field_expr))
            else:
                index = Variable(field_expr)
            
            return FieldReference(index)
        
        elif self.current_token.type == TokenType.IDENTIFIER:
            name = self.current_token.value
            self._advance()
            
            if self.current_token.type == TokenType.LPAREN:
                self._advance()  # Skip '('
                arguments = []
                
                if self.current_token.type != TokenType.RPAREN:
                    arguments.append(self._parse_expression())
                    
                    while self.current_token.type == TokenType.COMMA:
                        self._advance()  # Skip comma
                        arguments.append(self._parse_expression())
                
                self._expect(TokenType.RPAREN)
                return FunctionCall(name, arguments)
            
            elif self.current_token.type == TokenType.LBRACKET:
                self._advance()
                index = self._parse_expression()
                self._expect(TokenType.RBRACKET)
                return ArrayAccess(Variable(name), index)
            
            return Variable(name)
        
        elif self.current_token.type == TokenType.LPAREN:
            self._advance()
            if self.current_token.type == TokenType.RPAREN:
                raise SyntaxError("Empty parentheses are not allowed")
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return expr
        
        else:
            raise SyntaxError(f"Unexpected token: {self.current_token.type} at position {self.pos}")


def parse_awk_program(program_text: str, field_separator: Optional[str] = None) -> AwkProgram:
    
    lexer = AwkLexer(program_text)
    tokens = lexer.tokenize()
    
    parser = AwkParser(tokens)
    ast = parser.parse()
    ast.field_separator = field_separator
    
    return ast

if __name__ == "__main__":

    awk_program = "{print \"fields: \", $1, $2, $3, $NF, \"abc\", $0}"
    ast = parse_awk_program(awk_program)
    print(ast)

    print("--------------------------------")

    awk_program = "length($0) > 80"
    ast = parse_awk_program(awk_program)
    print(ast)

    print("--------------------------------")

    awk_program = "{ print $1 $1 }"
    ast = parse_awk_program(awk_program)
    print(ast)

    print("--------------------------------")

    awk_program = "{ if (x < length($0)) x = length($0) } END { print \"maximum line length is \" x }"
    ast = parse_awk_program(awk_program)
    print(ast)
    
    print("--------------------------------")

    program_text = "NR > 1 { printf \", \" } { printf \"%s\", $0 }"
    ast = parse_awk_program(program_text)
    print(ast)

    print("--------------------------------")
    
    program_text = "NR % \"$N_COLS\" == 1 { printf \"[\" }  { printf \"%s\", $0 }  {if (NR % \"$N_COLS\" == 0) { printf \"]\\n\" } else { printf \", \" }}"
    ast = parse_awk_program(program_text)
    print(ast)

    print("--------------------------------")
    program_text = """{
    key = sprintf("%s", $1);
    count[key]++;
    sum[key] += $3;
    sum_sq[key] += $3 * $3;
    if (!(key in max) || $3 > max[key]) max[key] = $3;
    if (!(key in min) || $3 < min[key]) min[key] = $3;
} 
END {
    for (key in max) {
        mean = sum[key] / count[key];
        variance = (sum_sq[key] / count[key]) - (mean * mean);
        stddev = (variance > 0) ? sqrt(variance) : 0;
        confidence_delta = 1.96 * stddev / sqrt(count[key]);
        normal_range_low = mean - confidence_delta;
        normal_range_high = mean + confidence_delta;
        printf "%s %s %s %.2f %.2f\n", key, min[key], max[key], normal_range_low, normal_range_high;
    }
}""".strip()

    ast = parse_awk_program(program_text)
    print(ast)



