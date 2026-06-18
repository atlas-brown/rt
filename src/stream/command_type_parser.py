from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Mapping, Optional

from stream.command_type import CommandType, PolymorphicCommandType, SimpleCommandType
from stream.regex_parser import RegexParser
from stream.regular_type import RegularType
from stream.transformation_ast import (
    ALPHA,
    ComposeTransform,
    ConcatenateTransform,
    ComplementTransform,
    DefaultIfEmptyStringTransform,
    DeleteCharsTransform,
    FieldSelectTransform,
    HeadLinesTransform,
    HoleNode,
    IntersectionTransform,
    KleenePlusTransform,
    KleeneStarTransform,
    LastFieldTransform,
    LineExtractTransform,
    OptionalTransform,
    ReverseTransform,
    SubtractionTransform,
    TaintTransform,
    TailLinesTransform,
    TransformationNode,
    TranslateCharsTransform,
    TranslateMatchTransform,
    UnionTransform,
    regex_ast_to_transform_node,
)


TYPE_VARIABLE_OUTPUT = "{{actual_input_type}}"
KNOWN_REGULAR_OPERATORS = {
    "identity",
    "id",
    "reverse",
    "compose",
    "translate_chars",
    "translate_match",
    "delete_chars",
    "field_select",
    "last_field",
    "line_extract",
    "head_lines",
    "tail_lines",
    "default_if_empty",
    "taint",
    "concat",
    "union",
    "intersect",
    "intersection",
    "subtract",
    "minus",
    "complement",
    "optional",
    "star",
    "plus",
}


@dataclass(frozen=True)
class ParsedCommandTypeAnnotation:
    input_type: str
    output_type: str
    polymorphic: bool = False
    variable_name: Optional[str] = None

    def to_command_type(self) -> CommandType:
        input_type = RegularType(self.input_type)
        if self.polymorphic:
            return PolymorphicCommandType(
                parse_transform_expression(self.output_type),
                input_type=input_type,
            )
        return SimpleCommandType(input_type, RegularType(self.output_type))

    def to_signature_data(self, command_name: str, match: dict) -> dict:
        data = {
            "command_name": command_name,
            "match": match,
            "default_input_type": self.input_type,
            "default_output_type": self.output_type if not self.polymorphic else ".*",
            "args": [],
            "flags": [],
            "rules": [],
            "isInteresting": True,
            "isTainted": False,
        }
        if self.polymorphic:
            data["rules"] = [
                {
                    "condition": {},
                    "update": {"output_type": self.output_type},
                }
            ]
        return data


def parse_command_type_annotation(annotation: str) -> ParsedCommandTypeAnnotation:
    annotation = annotation.strip()
    variable_name = None
    body = annotation

    forall_match = re.match(
        r"^(?:forall|∀)\s+([A-Za-z_][A-Za-z0-9_]*|α)\s*\.\s*(.+)$",
        annotation,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if forall_match is not None:
        variable_name = forall_match.group(1)
        body = forall_match.group(2).strip()

    input_text, output_text = _split_arrow(body)
    if variable_name is not None:
        aliases = {variable_name, f"{{{{{variable_name}}}}}"}
        if variable_name != "α":
            aliases.add("α")
            aliases.add("{{α}}")
        input_type = ".*" if input_text.strip() in aliases else _normalize_type_variable(input_text, variable_name)
        output_type = _normalize_type_variable(output_text, variable_name)
        parse_transform_expression(output_type)
        return ParsedCommandTypeAnnotation(
            input_type=input_type,
            output_type=output_type,
            polymorphic=True,
            variable_name=variable_name,
        )

    RegularType(input_text)
    output_call = _parse_call(output_text)
    if output_call is not None and _canonical_operator_name(output_call[0]) in KNOWN_REGULAR_OPERATORS:
        parse_transform_expression(output_text)
        return ParsedCommandTypeAnnotation(
            input_type=input_text,
            output_type=output_text,
            polymorphic=True,
        )

    # Validate both sides while preserving the user-facing regex text.
    RegularType(output_text)
    return ParsedCommandTypeAnnotation(input_type=input_text, output_type=output_text)


def parse_transform_expression(
    expression: str,
    hole_transforms: Optional[Mapping[str, TransformationNode]] = None,
) -> TransformationNode:
    expression = expression.strip()
    if not expression:
        return regex_ast_to_transform_node(RegexParser("").parse(), hole_transforms)

    if expression in {"α", "actual_input_type", TYPE_VARIABLE_OUTPUT}:
        return ALPHA

    hole_match = re.fullmatch(r"\{\{\s*([^{}]+?)\s*\}\}", expression)
    if hole_match is not None:
        hole_name = hole_match.group(1)
        if hole_transforms and hole_name in hole_transforms:
            return hole_transforms[hole_name]
        if hole_name in {"actual_input_type", "α"}:
            return ALPHA
        return HoleNode(hole_name)

    call = _parse_call(expression)
    if call is not None:
        name, positional, keyword = call
        if _canonical_operator_name(name) in KNOWN_REGULAR_OPERATORS:
            return _build_operator_transform(name, positional, keyword, hole_transforms)

    return regex_ast_to_transform_node(RegexParser(expression).parse(), hole_transforms)


def _split_arrow(body: str) -> tuple[str, str]:
    index = _find_top_level_token(body, "->")
    if index < 0:
        raise ValueError("Command type annotation must contain a top-level '->'")
    left = body[:index].strip()
    right = body[index + 2 :].strip()
    if not left or not right:
        raise ValueError("Command type annotation must include both input and output types")
    return left, right


def _normalize_type_variable(expression: str, variable_name: str) -> str:
    expression = expression.strip()
    if _is_string_literal(expression):
        return expression

    aliases = {variable_name, f"{{{{{variable_name}}}}}"}
    if variable_name != "α":
        aliases.add("α")
        aliases.add("{{α}}")
    if expression in aliases:
        return TYPE_VARIABLE_OUTPUT

    expression = re.sub(
        r"\{\{\s*" + re.escape(variable_name) + r"\s*\}\}",
        TYPE_VARIABLE_OUTPUT,
        expression,
    )
    if variable_name != "α":
        expression = re.sub(r"\{\{\s*α\s*\}\}", TYPE_VARIABLE_OUTPUT, expression)

    call = _parse_call(expression)
    if call is None:
        return _normalize_regex_type_variable(expression, variable_name)

    name, positional, keyword = call
    canonical = _canonical_operator_name(name)
    expression_args = _operator_expression_arg_indices(canonical, len(positional))
    normalized_positional = [
        _normalize_type_variable(arg, variable_name)
        if index in expression_args and not _is_string_literal(arg)
        else arg
        for index, arg in enumerate(positional)
    ]
    return _render_call(name, normalized_positional, keyword)


def _normalize_regex_type_variable(expression: str, variable_name: str) -> str:
    from stream.regex_parser import RegexParser, ast_to_regex

    regex_ast = RegexParser(expression).parse()
    normalized_ast = _replace_type_variable_atom(regex_ast, variable_name)
    return ast_to_regex(normalized_ast)


def _replace_type_variable_atom(regex_node, variable_name: str):
    from stream.regex_parser import (
        CharacterClass,
        Complement,
        Concatenate,
        Dot,
        EmptyLanguageNode,
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

    if isinstance(regex_node, Literal):
        if len(variable_name) == 1 and regex_node.char == variable_name:
            return Hole("actual_input_type")
        if regex_node.char == "α":
            return Hole("actual_input_type")
        return regex_node
    if isinstance(regex_node, Hole):
        if regex_node.name in {variable_name, "α", "actual_input_type"}:
            return Hole("actual_input_type")
        return regex_node
    if isinstance(regex_node, Concatenate):
        return Concatenate([
            _replace_type_variable_atom(node, variable_name)
            for node in regex_node.nodes
        ])
    if isinstance(regex_node, Union):
        return Union(
            _replace_type_variable_atom(regex_node.left, variable_name),
            _replace_type_variable_atom(regex_node.right, variable_name),
        )
    if isinstance(regex_node, Intersection):
        return Intersection(
            _replace_type_variable_atom(regex_node.left, variable_name),
            _replace_type_variable_atom(regex_node.right, variable_name),
        )
    if isinstance(regex_node, Complement):
        return Complement(_replace_type_variable_atom(regex_node.node, variable_name))
    if isinstance(regex_node, Repeat):
        return Repeat(
            _replace_type_variable_atom(regex_node.node, variable_name),
            regex_node.min,
            regex_node.max,
        )
    if isinstance(regex_node, (CharacterClass, Range, PosixClass, Dot, StartAnchor, EndAnchor, EmptyLanguageNode)):
        return regex_node
    return regex_node


def _operator_expression_arg_indices(canonical_name: str, arg_count: int) -> set[int]:
    if canonical_name == "compose":
        return {0, 1}
    if canonical_name == "default_if_empty":
        return {0, 1}
    if canonical_name in {
        "concat",
        "union",
        "intersect",
        "intersection",
        "subtract",
        "minus",
    }:
        return {0, 1}
    if canonical_name in {"translate_match", "line_extract"}:
        return {0, 1}
    if canonical_name in {
        "reverse",
        "translate_chars",
        "delete_chars",
        "field_select",
        "last_field",
        "head_lines",
        "tail_lines",
        "taint",
        "complement",
        "optional",
        "star",
        "plus",
        "identity",
        "id",
    }:
        return {0}
    return set(range(arg_count))


def _render_call(name: str, positional: list[str], keyword: dict[str, str]) -> str:
    args = list(positional)
    args.extend(f"{key}={value}" for key, value in keyword.items())
    return f"{name}({', '.join(args)})"


def _build_operator_transform(
    name: str,
    positional: list[str],
    keyword: dict[str, str],
    hole_transforms: Optional[Mapping[str, TransformationNode]],
) -> TransformationNode:
    canonical = _canonical_operator_name(name)

    def expr(index: int) -> TransformationNode:
        return parse_transform_expression(_required_positional(canonical, positional, index), hole_transforms)

    if canonical in {"identity", "id"}:
        _require_arity(canonical, positional, 1)
        return expr(0)
    if canonical == "reverse":
        _require_arity(canonical, positional, 1)
        return ReverseTransform(expr(0))
    if canonical == "compose":
        _require_arity(canonical, positional, 2)
        return ComposeTransform(expr(0), expr(1))
    if canonical == "translate_chars":
        _require_arity(canonical, positional, 3)
        return TranslateCharsTransform(
            expr(0),
            _string_arg(positional[1]),
            _string_arg(positional[2]),
            invert=_bool_kw(keyword, "invert", False),
            squeeze=_bool_kw(keyword, "squeeze", False),
            stream=_bool_kw(keyword, "stream", False),
        )
    if canonical == "delete_chars":
        _require_arity(canonical, positional, 2)
        return DeleteCharsTransform(
            expr(0),
            _string_arg(positional[1]),
            invert=_bool_kw(keyword, "invert", False),
            stream=_bool_kw(keyword, "stream", False),
        )
    if canonical == "field_select":
        _require_arity(canonical, positional, 3)
        return FieldSelectTransform(
            expr(0),
            _string_arg(positional[1]),
            _string_arg(positional[2]),
            invert=_bool_kw(keyword, "invert", False),
        )
    if canonical == "last_field":
        _require_arity(canonical, positional, 2)
        return LastFieldTransform(expr(0), _string_arg(positional[1]))
    if canonical == "translate_match":
        _require_arity(canonical, positional, 3)
        pattern = (
            _string_arg(positional[1])
            if _is_string_literal(positional[1])
            else parse_transform_expression(positional[1], hole_transforms)
        )
        return TranslateMatchTransform(
            expr(0),
            pattern,
            _string_arg(positional[2]),
            global_match=_bool_kw(keyword, "global", _bool_kw(keyword, "global_match", False)),
            mode=_string_kw(keyword, "mode", "compat"),
            stream=_bool_kw(keyword, "stream", False),
        )
    if canonical == "line_extract":
        _require_arity(canonical, positional, 2)
        pattern = (
            _string_arg(positional[1])
            if _is_string_literal(positional[1])
            else parse_transform_expression(positional[1], hole_transforms)
        )
        return LineExtractTransform(expr(0), pattern)
    if canonical == "head_lines":
        _require_arity(canonical, positional, 2)
        return HeadLinesTransform(expr(0), _int_arg(positional[1]))
    if canonical == "tail_lines":
        _require_arity(canonical, positional, 2)
        return TailLinesTransform(expr(0), _int_arg(positional[1]))
    if canonical == "default_if_empty":
        _require_arity(canonical, positional, 2)
        return DefaultIfEmptyStringTransform(expr(0), expr(1))
    if canonical == "taint":
        _require_arity(canonical, positional, 2)
        return TaintTransform(expr(0), _bool_arg(positional[1]))
    if canonical == "concat":
        _require_arity(canonical, positional, 2)
        return ConcatenateTransform(expr(0), expr(1))
    if canonical == "union":
        _require_arity(canonical, positional, 2)
        return UnionTransform(expr(0), expr(1))
    if canonical in {"intersect", "intersection"}:
        _require_arity(canonical, positional, 2)
        return IntersectionTransform(expr(0), expr(1))
    if canonical in {"subtract", "minus"}:
        _require_arity(canonical, positional, 2)
        return SubtractionTransform(expr(0), expr(1))
    if canonical == "complement":
        _require_arity(canonical, positional, 1)
        return ComplementTransform(expr(0))
    if canonical == "optional":
        _require_arity(canonical, positional, 1)
        return OptionalTransform(expr(0))
    if canonical == "star":
        _require_arity(canonical, positional, 1)
        return KleeneStarTransform(expr(0))
    if canonical == "plus":
        _require_arity(canonical, positional, 1)
        return KleenePlusTransform(expr(0))

    raise ValueError(f"Unknown regular operator: {name}")


def _canonical_operator_name(name: str) -> str:
    return name.strip().replace("-", "_")


def _required_positional(name: str, positional: list[str], index: int) -> str:
    if index >= len(positional):
        raise ValueError(f"{name} expects argument {index + 1}")
    return positional[index]


def _require_arity(name: str, positional: list[str], expected: int) -> None:
    if len(positional) != expected:
        raise ValueError(f"{name} expects {expected} positional arguments, got {len(positional)}")


def _string_arg(value: str) -> str:
    value = value.strip()
    if not _is_string_literal(value):
        return value
    parsed = ast.literal_eval(value)
    if not isinstance(parsed, str):
        raise ValueError(f"Expected string argument, got {value}")
    return parsed


def _string_kw(keyword: dict[str, str], name: str, default: str) -> str:
    if name not in keyword:
        return default
    return _string_arg(keyword[name])


def _int_arg(value: str) -> int:
    try:
        return int(value.strip())
    except ValueError as exc:
        raise ValueError(f"Expected integer argument, got {value}") from exc


def _bool_arg(value: str) -> bool:
    value = value.strip().lower()
    if value in {"true", "1", "yes"}:
        return True
    if value in {"false", "0", "no"}:
        return False
    raise ValueError(f"Expected boolean argument, got {value}")


def _bool_kw(keyword: dict[str, str], name: str, default: bool) -> bool:
    if name not in keyword:
        return default
    return _bool_arg(keyword[name])


def _is_string_literal(value: str) -> bool:
    value = value.strip()
    return len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}


def _parse_call(expression: str) -> Optional[tuple[str, list[str], dict[str, str]]]:
    expression = expression.strip()
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*\(", expression)
    if match is None or not expression.endswith(")"):
        return None

    open_index = expression.find("(", match.end(1))
    if _matching_close_paren(expression, open_index) != len(expression) - 1:
        return None

    name = match.group(1)
    inner = expression[open_index + 1 : -1].strip()
    if not inner:
        return name, [], {}

    positional: list[str] = []
    keyword: dict[str, str] = {}
    for arg in _split_top_level(inner, ","):
        key_value = _split_top_level_assignment(arg)
        if key_value is None:
            positional.append(arg.strip())
        else:
            key, value = key_value
            keyword[key.strip()] = value.strip()
    return name, positional, keyword


def _matching_close_paren(text: str, open_index: int) -> int:
    depth = 0
    quote: Optional[str] = None
    escaped = False
    for index in range(open_index, len(text)):
        char = text[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
    return -1


def _split_top_level_assignment(text: str) -> Optional[tuple[str, str]]:
    index = _find_top_level_token(text, "=")
    if index < 0:
        return None
    return text[:index], text[index + 1 :]


def _split_top_level(text: str, delimiter: str) -> list[str]:
    parts = []
    start = 0
    index = 0
    while index < len(text):
        if text.startswith(delimiter, index) and _is_top_level_at(text, index):
            parts.append(text[start:index].strip())
            index += len(delimiter)
            start = index
            continue
        index += 1
    parts.append(text[start:].strip())
    return parts


def _find_top_level_token(text: str, token: str) -> int:
    index = 0
    while index < len(text):
        if text.startswith(token, index) and _is_top_level_at(text, index):
            return index
        index += 1
    return -1


def _is_top_level_at(text: str, target_index: int) -> bool:
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    quote: Optional[str] = None
    escaped = False
    index = 0
    while index < target_index:
        char = text[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
        elif char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth -= 1
        elif char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth -= 1
        elif char == "{" and not text.startswith("{{", index):
            brace_depth += 1
        elif char == "}" and not text.startswith("}}", index):
            brace_depth -= 1
        index += 1
    return paren_depth == 0 and bracket_depth == 0 and brace_depth == 0 and quote is None
