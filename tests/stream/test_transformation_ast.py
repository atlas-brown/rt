import pytest

from stream.regex_parser import (
    CharacterClass,
    Complement,
    Concatenate,
    Dot,
    EndAnchor,
    Hole,
    Intersection,
    Literal,
    PosixClass,
    Range,
    Repeat,
    StartAnchor,
    Union,
)
from stream.regular_type import RegularType
from stream.tool_error import ToolError
from stream.transformation_ast import (
    ComplementTransform,
    ComposeTransform,
    ConcatenateTransform,
    ConstantTransform,
    FieldSelectTransform,
    HeadLinesTransform,
    HoleNode,
    IntersectionTransform,
    RegexPatternTransform,
    TailLinesTransform,
    TranslateCharsTransform,
    UnionTransform,
    regex_ast_to_transform_node,
)

# ---------------------------------------------------------------------------
# Leaf / basic nodes
# ---------------------------------------------------------------------------


def test_constant_transform_applies_to_env():
    ct = ConstantTransform(RegularType("abc"))
    result = ct.apply({})
    assert result.pattern == "abc"


def test_regex_pattern_transform_applies_to_env():
    rt = RegexPatternTransform("[a-z]+", mode="compat", repr_mode="line", tainted=False)
    result = rt.apply({})
    assert result.pattern == "[a-z]+"
    assert result.repr_mode == "line"
    assert result.tainted is False


def test_hole_node_applies_to_env():
    hn = HoleNode("my_hole")
    env = {"my_hole": RegularType("xyz")}
    result = hn.apply(env)
    assert result.pattern == "xyz"


# ---------------------------------------------------------------------------
# ComposeTransform
# ---------------------------------------------------------------------------


def test_compose_transform_with_normalize_input_to_line_on_line_based_type():
    inner = RegexPatternTransform("[a-z]+", repr_mode="line")
    outer = HoleNode("actual_input_type")
    compose = ComposeTransform(outer, inner, normalize_input_to_line=True)
    result = compose.apply({})
    assert result.repr_mode == "line"
    assert result.pattern == "[a-z]+"


# ---------------------------------------------------------------------------
# FieldSelectTransform._parse_indices
# ---------------------------------------------------------------------------


def test_field_select_parse_indices_empty_string():
    indices, has_upperbound = FieldSelectTransform._parse_indices("")
    assert indices == []
    assert has_upperbound is False


def test_field_select_parse_indices_single_fields():
    indices, has_upperbound = FieldSelectTransform._parse_indices("1,3")
    assert indices == [1, 3]
    assert has_upperbound is True


def test_field_select_parse_indices_open_ended_range():
    indices, has_upperbound = FieldSelectTransform._parse_indices("3-")
    assert indices == [3]
    assert has_upperbound is False


def test_field_select_parse_indices_invalid_range_raises_tool_error():
    with pytest.raises(ToolError):
        FieldSelectTransform._parse_indices("1-2-3")


# ---------------------------------------------------------------------------
# HeadLinesTransform / TailLinesTransform
# ---------------------------------------------------------------------------


def test_head_lines_transform_fst_path_for_small_line_count():
    head = HeadLinesTransform(RegexPatternTransform(".*", repr_mode="stream"), 3)
    result = head.apply({})
    assert result.repr_mode == "stream"


def test_head_lines_transform_line_based_for_large_line_count():
    head = HeadLinesTransform(RegexPatternTransform(".*", repr_mode="stream"), 10)
    result = head.apply({})
    assert result.repr_mode == "line"


def test_tail_lines_transform_fst_path_for_small_line_count():
    tail = TailLinesTransform(RegexPatternTransform(".*", repr_mode="stream"), 5)
    result = tail.apply({})
    assert result.repr_mode == "stream"


def test_tail_lines_transform_line_based_for_large_line_count():
    tail = TailLinesTransform(RegexPatternTransform(".*", repr_mode="stream"), 10)
    result = tail.apply({})
    assert result.repr_mode == "line"


# ---------------------------------------------------------------------------
# TranslateCharsTransform flags
# ---------------------------------------------------------------------------


def test_translate_chars_line_delimited_modifies_output():
    input_node = RegexPatternTransform("aa", repr_mode="line")
    default = TranslateCharsTransform(input_node, "a", "x").apply({})
    line_delimited = TranslateCharsTransform(
        input_node, "a", "x", line_delimited=True
    ).apply({})
    assert line_delimited.repr_mode == "line"
    # line_delimited must produce a different automaton than the default path
    assert line_delimited.get_shortest_example() != default.get_shortest_example()


def test_translate_chars_squeeze_modifies_output():
    input_node = RegexPatternTransform("aa", repr_mode="line")
    result = TranslateCharsTransform(input_node, "a", "x", squeeze=True).apply({})
    assert result.repr_mode == "line"
    assert result.get_shortest_example() == "x"


def test_translate_chars_invert_modifies_output():
    input_node = RegexPatternTransform("abc", repr_mode="line")
    result = TranslateCharsTransform(input_node, "a", "x", invert=True).apply({})
    assert result.repr_mode == "line"
    assert result.get_shortest_example() == "axx"


# ---------------------------------------------------------------------------
# regex_ast_to_transform_node
# ---------------------------------------------------------------------------


def test_regex_ast_to_transform_node_literal():
    node = Literal("a")
    result = regex_ast_to_transform_node(node)
    assert isinstance(result, RegexPatternTransform)
    assert result.pattern == "a"


def test_regex_ast_to_transform_node_dot():
    node = Dot()
    result = regex_ast_to_transform_node(node)
    assert isinstance(result, RegexPatternTransform)
    assert result.pattern == "."


def test_regex_ast_to_transform_node_concatenate():
    node = Concatenate([Literal("a"), Literal("b")])
    result = regex_ast_to_transform_node(node)
    assert isinstance(result, ConcatenateTransform)


def test_regex_ast_to_transform_node_union():
    node = Union(Literal("a"), Literal("b"))
    result = regex_ast_to_transform_node(node)
    assert isinstance(result, UnionTransform)


def test_regex_ast_to_transform_node_intersection():
    node = Intersection(Literal("a"), Literal("b"))
    result = regex_ast_to_transform_node(node)
    assert isinstance(result, IntersectionTransform)


def test_regex_ast_to_transform_node_complement():
    node = Complement(Literal("a"))
    result = regex_ast_to_transform_node(node)
    assert isinstance(result, ComplementTransform)


def test_regex_ast_to_transform_node_repeat_star():
    node = Repeat(Literal("a"), 0, None)
    result = regex_ast_to_transform_node(node)
    assert isinstance(result, RegexPatternTransform) or isinstance(
        result, type(regex_ast_to_transform_node(Repeat(Literal("a"), 0, None)))
    )
    # The implementation maps 0,None to KleeneStarTransform
    from stream.transformation_ast import KleeneStarTransform

    assert isinstance(result, KleeneStarTransform)


def test_regex_ast_to_transform_node_repeat_plus():
    from stream.transformation_ast import KleenePlusTransform

    node = Repeat(Literal("a"), 1, None)
    result = regex_ast_to_transform_node(node)
    assert isinstance(result, KleenePlusTransform)


def test_regex_ast_to_transform_node_repeat_optional():
    from stream.transformation_ast import OptionalTransform

    node = Repeat(Literal("a"), 0, 1)
    result = regex_ast_to_transform_node(node)
    assert isinstance(result, OptionalTransform)


def test_regex_ast_to_transform_node_character_class():
    node = CharacterClass(False, [Literal("a")])
    result = regex_ast_to_transform_node(node)
    assert isinstance(result, RegexPatternTransform)


def test_regex_ast_to_transform_node_range():
    node = Range("a", "z")
    result = regex_ast_to_transform_node(node)
    assert isinstance(result, RegexPatternTransform)
    assert result.pattern == "[a-z]"


def test_regex_ast_to_transform_node_posix_class():
    node = PosixClass("digit")
    result = regex_ast_to_transform_node(node)
    assert isinstance(result, RegexPatternTransform)
    assert result.pattern == "[:digit:]"


def test_regex_ast_to_transform_node_start_anchor():
    node = StartAnchor()
    result = regex_ast_to_transform_node(node)
    assert isinstance(result, RegexPatternTransform)
    assert result.pattern == "^"


def test_regex_ast_to_transform_node_end_anchor():
    node = EndAnchor()
    result = regex_ast_to_transform_node(node)
    assert isinstance(result, RegexPatternTransform)
    assert result.pattern == "$"


def test_regex_ast_to_transform_node_hole():
    node = Hole("alpha")
    result = regex_ast_to_transform_node(node)
    assert isinstance(result, HoleNode)
    assert result.name == "alpha"
