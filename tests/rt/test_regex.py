import pytest
from hypothesis import given
from hypothesis import strategies as st

from rt.regex import ast
from rt.regex.parser import Dialect, ParseError


@pytest.mark.parametrize(
    ("pattern", "expected"),
    [
        ("a", ast.Literal("a")),
        (
            "ab*",
            ast.Concatenation(
                ast.Literal("a"), ast.Repetition(ast.Literal("b"), 0, None)
            ),
        ),
        (
            "a|bc",
            ast.Union(
                ast.Literal("a"),
                ast.Concatenation(ast.Literal("b"), ast.Literal("c")),
            ),
        ),
        (
            "(a|b)c",
            ast.Concatenation(
                ast.Union(ast.Literal("a"), ast.Literal("b")),
                ast.Literal("c"),
            ),
        ),
        ("((a))", ast.Literal("a")),
        ("", ast.Epsilon()),
        ("a|", ast.Union(ast.Literal("a"), ast.Epsilon())),
        ("|b", ast.Union(ast.Epsilon(), ast.Literal("b"))),
        (
            "a|b|c",
            ast.Union(ast.Union(ast.Literal("a"), ast.Literal("b")), ast.Literal("c")),
        ),
        (
            "abc",
            ast.Concatenation(
                ast.Literal("a"),
                ast.Concatenation(ast.Literal("b"), ast.Literal("c")),
            ),
        ),
        (
            "(a*)*",
            ast.Repetition(ast.Repetition(ast.Literal("a"), 0, None), 0, None),
        ),
        (
            "(a|b)*c|d*",
            ast.Union(
                ast.Concatenation(
                    ast.Repetition(
                        ast.Union(ast.Literal("a"), ast.Literal("b")), 0, None
                    ),
                    ast.Literal("c"),
                ),
                ast.Repetition(ast.Literal("d"), 0, None),
            ),
        ),
    ],
)
def test_parse_shapes(pattern: str, expected: ast.Regex, parse) -> None:
    """Validate key parser AST shapes for precedence, grouping, and chaining."""
    assert parse(pattern) == expected


def test_parse_literal_round_trip(parse, unparse) -> None:
    node = parse("a")
    assert node == ast.Literal("a")
    assert unparse(node) == "a"


@pytest.mark.parametrize(
    ("input_char", "escaped"),
    [
        ("*", r"\*"),
        ("|", r"\|"),
        ("(", r"\("),
        (")", r"\)"),
        ("[", r"\["),
        ("]", r"\]"),
        (".", r"\."),
        ("^", r"\^"),
        ("$", r"\$"),
        ("~", r"\~"),
        ("&", r"\&"),
        ("\\", r"\\"),
    ],
)
def test_parse_format_escaped_metachars(
    input_char: str,
    escaped: str,
    parse,
    unparse,
) -> None:
    node = parse(escaped)
    assert node == ast.Literal(input_char)
    assert unparse(node) == escaped


def test_literal_boundary_characters(parse, unparse) -> None:
    assert parse(r"\s") == ast.Literal(" ")
    assert parse(r"\n") == ast.Literal("\n")
    assert parse(r"\t") == ast.Literal("\t")

    assert unparse(ast.Literal(" ")) == " "
    assert unparse(ast.Literal("\n")) == "\n"
    assert unparse(ast.Literal("\t")) == "\t"


def test_format_minimal_parentheses_union(unparse) -> None:
    assert unparse(ast.Union(ast.Literal("a"), ast.Literal("b"))) == "a|b"


def test_format_parentheses_for_precedence(unparse) -> None:
    node = ast.Concatenation(
        ast.Union(ast.Literal("a"), ast.Literal("b")), ast.Literal("c")
    )
    assert unparse(node) == "(a|b)c"


@pytest.mark.parametrize(
    ("pattern", "dialect", "expected"),
    [
        (r"a\|b", Dialect.BRE, ast.Union(ast.Literal("a"), ast.Literal("b"))),
        (r"a\+", Dialect.BRE, ast.Repetition(ast.Literal("a"), 1, None)),
        (
            r"\(a\|b\)",
            Dialect.BRE,
            ast.Union(ast.Literal("a"), ast.Literal("b")),
        ),
    ],
)
def test_bre_mode_examples(
    pattern: str, dialect: Dialect, expected: ast.Regex, parse
) -> None:
    """Validate representative BRE parsing behavior for escaped operators and groups."""
    assert parse(pattern, dialect=dialect) == expected


def test_parse_hole_basic(parse) -> None:
    assert parse("{{name}}") == ast.Hole("name")


def test_parse_hole_empty_name(parse) -> None:
    assert parse("{{}}") == ast.Hole("")


def test_parse_hole_whitespace(parse) -> None:
    assert parse("{{  name  }}") == ast.Hole("name")


def test_parse_hole_single_brace_in_name(parse) -> None:
    assert parse("{{a}b}}") == ast.Hole("a}b")


def test_parse_hole_unterminated_error(parse) -> None:
    with pytest.raises(ParseError):
        parse("{{unclosed")


@pytest.mark.parametrize(
    ("pattern", "msg"),
    [
        ("(a", "Missing closing parenthesis"),
        ("[abc", "Unterminated character class"),
        ("a{1", "Quantifier must end with"),
        ("a\\", "Escape character"),
        ("[[:unknown:]]", "Unknown POSIX character class"),
    ],
)
def test_parse_errors(pattern: str, msg: str, parse) -> None:
    """Verify malformed expressions raise ParseError for known failure classes."""
    # Do not match the exact message, it might change in the future.
    with pytest.raises(ParseError, match=msg):
        parse(pattern)


def test_parse_lonely_bar_is_epsilon_union(parse) -> None:
    """Ensure a lone '|' parses as an epsilon-on-both-sides union."""
    assert parse("|") == ast.Union(ast.Epsilon(), ast.Epsilon())


def test_parse_leading_star_errors(parse) -> None:
    """Ensure a leading '*' is rejected because repetition needs a target."""
    with pytest.raises(ParseError):
        parse("*a")


def test_format_anchor_mapping(unparse) -> None:
    assert unparse(ast.StartAnchor()) == "^"
    assert unparse(ast.EndAnchor()) == "$"


def test_format_posix_class_in_character_class(unparse) -> None:
    node = ast.CharacterClass(False, [ast.PosixClass.DIGIT])
    assert unparse(node) == "[[:digit:]]"


_CURATED_PATTERNS = [
    "a",
    "ab",
    "a|b",
    "a*",
    "a+",
    "a?",
    "a{2,4}",
    "(a|b)c",
    "(a|b)*c|d*",
    "[abc]",
    "[a-z]",
    "[^abc]",
    ".+",
    "{{x}}",
]


@given(pattern=st.sampled_from(_CURATED_PATTERNS))
def test_property_round_trip_curated_patterns(pattern: str, parse, unparse) -> None:
    node = parse(pattern)
    reparsed = parse(unparse(node))
    assert reparsed == node


_safe_literal_chars = st.characters(
    blacklist_characters="^$.*+?{}[]()|&~\\\n\r\t\v\f\b",
    min_codepoint=32,
    max_codepoint=126,
)


def canonical_atom() -> st.SearchStrategy[ast.Regex]:
    leaf = st.one_of(
        _safe_literal_chars.map(ast.Literal), st.just(ast.Dot()), st.just(ast.Hole("x"))
    )
    rep_bounds = st.sampled_from([(0, None), (1, None), (0, 1), (2, 2), (1, 3)])
    rep = st.tuples(leaf, rep_bounds).map(
        lambda v: ast.Repetition(v[0], v[1][0], v[1][1])
    )
    return st.one_of(leaf, rep)


@st.composite
def canonical_ast(draw) -> ast.Regex:
    atom = canonical_atom()
    maybe_binary = st.one_of(
        atom,
        st.tuples(atom, atom).map(lambda v: ast.Union(v[0], v[1])),
        st.tuples(atom, atom).map(lambda v: ast.Concatenation(v[0], v[1])),
    )
    return draw(maybe_binary)


@given(node=canonical_ast())
def test_property_ast_round_trip_canonical_subset(
    node: ast.Regex, parse, unparse
) -> None:
    assert parse(unparse(node)) == node


@given(text=st.text())
def test_property_parser_defensive_random_text(text: str, parse) -> None:
    """Property: random text never crashes parser outside expected error classes."""
    try:
        parse(text)
    except ParseError:
        pass


def fully_parenthesized(regex: ast.Regex) -> str:
    match regex:
        case ast.EmptyLanguage() | ast.Epsilon():
            return ""
        case ast.Dot():
            return "."
        case ast.StartAnchor():
            return "^"
        case ast.EndAnchor():
            return "$"
        case ast.Literal(char):
            if char in "^$.*+?{}[]()|&~\\":
                return f"\\{char}"
            return char
        case ast.Hole(name):
            return f"{{{{{name}}}}}"
        case ast.Complement(node):
            return f"(~{fully_parenthesized(node)})"
        case ast.Concatenation(left, right):
            return f"({fully_parenthesized(left)}{fully_parenthesized(right)})"
        case ast.Union(left, right):
            return f"({fully_parenthesized(left)}|{fully_parenthesized(right)})"
        case ast.Intersection(left, right):
            return f"({fully_parenthesized(left)}&{fully_parenthesized(right)})"
        case ast.Repetition(node, min_count, max_count):
            base = f"({fully_parenthesized(node)})"
            if min_count == 0 and max_count is None:
                return f"({base}*)"
            if min_count == 1 and max_count is None:
                return f"({base}+)"
            if min_count == 0 and max_count == 1:
                return f"({base}?)"
            if max_count is None:
                return f"({base}{{{min_count},}})"
            if min_count == max_count:
                return f"({base}{{{min_count}}})"
            return f"({base}{{{min_count},{max_count}}})"
        case ast.CharacterClass(is_negated, items):
            body = ""
            for item in items:
                if isinstance(item, str):
                    body += "\\]" if item == "]" else item
                elif isinstance(item, ast.Range):
                    body += f"{item.start}-{item.end}"
                else:
                    body += f"[[:{item.value}:]]"
            return f"[{'^' if is_negated else ''}{body}]"
        case _:
            raise AssertionError(f"Unexpected node type: {type(regex)}")


@given(node=canonical_ast())
def test_property_format_length_leq_fully_parenthesized(
    node: ast.Regex, unparse
) -> None:
    """Property: formatter output is no longer than a fully parenthesized representation."""
    assert len(unparse(node)) <= len(fully_parenthesized(node))
