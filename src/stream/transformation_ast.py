from typing import Dict, List, Optional, Set, Tuple, Union, Any, Mapping
from stream.regular_type import RegularType
import re

from stream.tool_error import ToolError


def clone_regular_type(regular_type: RegularType) -> RegularType:
    if regular_type.pattern is not None:
        return RegularType(
            regular_type.pattern,
            tainted=regular_type.tainted,
        )
    return RegularType(
        automaton=regular_type.nfa.clone(),
        tainted=regular_type.tainted,
    )


def _approximate_translate_chars_without_fst(source_chars: str, target_chars: str, squeeze: bool, tainted: bool) -> RegularType:
    if squeeze:
        if not target_chars:
            return RegularType(".*", tainted=tainted)
        output_chars = set()
        for index, _ in enumerate(source_chars):
            output_chars.add(target_chars[index] if index < len(target_chars) else target_chars[-1])
        excluded_chars = "".join(ch for ch in source_chars if ch not in output_chars)
        return _type_excluding_chars(excluded_chars, tainted)
    return RegularType(".*", tainted=tainted)


def _type_excluding_chars(chars: str, tainted: bool) -> RegularType:
    char_class = _regex_char_class(chars)
    if not char_class:
        return RegularType(".*", tainted=tainted)
    return RegularType(f"~(.*[{char_class}].*)", tainted=tainted)


def _regex_char_class(chars: str) -> str:
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

class TransformationNode:
    """Base class for all AST nodes in the transformation tree."""
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        """
        Apply this transformation with the given environment mapping.
        
        Args:
            env: A mapping from hole names to their corresponding RegularType values
        
        Returns:
            The resulting RegularType after applying the transformation
        """
        raise NotImplementedError("Subclasses must implement apply")
    
    def __repr__(self) -> str:
        return self.__class__.__name__

# ======== Holes and basic transformations ========

class HoleNode(TransformationNode):
    """A hole node that gets filled with a value from the environment."""
    def __init__(self, name: str):
        self.name = name
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        if self.name not in env:
            raise ToolError(f"Hole '{self.name}' not found in environment")
        return env[self.name]
    
    def __repr__(self) -> str:
        return self.name

class ConstantTransform(TransformationNode):
    """A transformation that returns a constant type, ignoring the environment."""
    def __init__(self, output_type: RegularType):
        self.output_type = output_type
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        return clone_regular_type(self.output_type)
    
    def __repr__(self) -> str:
        return f"Constant({self.output_type})"

class RegexPatternTransform(TransformationNode):
    """A transformation that creates a RegularType from a regex pattern."""
    def __init__(self, pattern: str, mode: str = "compat", tainted: bool = True):
        self.pattern = pattern
        self.mode = mode
        self.tainted = tainted
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        return RegularType(self.pattern, mode=self.mode, tainted=self.tainted)
    
    def __repr__(self) -> str:
        return f"RegexPattern('{self.pattern}')"


class TaintTransform(TransformationNode):
    """Attach analysis taint metadata to a type expression."""
    def __init__(self, inner: TransformationNode, tainted: bool):
        self.inner = inner
        self.tainted = tainted

    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        result = self.inner.apply(env)
        result.tainted = self.tainted
        return result

    def __repr__(self) -> str:
        return f"taint({self.inner}, {self.tainted})"


class ComposeTransform(TransformationNode):
    """Apply one transformation to the type produced by another transformation."""
    def __init__(
        self,
        outer: TransformationNode,
        inner: TransformationNode,
        output_tainted: Optional[bool] = None,
    ):
        self.outer = outer
        self.inner = inner
        self.output_tainted = output_tainted

    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        actual_input = self.inner.apply(env)

        child_env = dict(env)
        child_env["α"] = actual_input
        child_env["actual_input_type"] = actual_input
        result = self.outer.apply(child_env)
        if self.output_tainted is not None:
            result.tainted = self.output_tainted
        return result

    def __repr__(self) -> str:
        return f"compose({self.outer}, {self.inner})"

# ======== Regular language operations ========

class IntersectionTransform(TransformationNode):
    """A transformation that intersects the result of two transformations."""
    def __init__(self, left: TransformationNode, right: TransformationNode):
        self.left = left
        self.right = right
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        left_result = self.left.apply(env)
        right_result = self.right.apply(env)
        return left_result & right_result
    
    def __repr__(self) -> str:
        return f"({self.left} & {self.right})"

class ConcatenateTransform(TransformationNode):
    """A transformation that concatenates the results of two transformations."""
    def __init__(self, left: TransformationNode, right: TransformationNode):
        self.left = left
        self.right = right
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        left_result = self.left.apply(env)
        right_result = self.right.apply(env)
        return left_result + right_result
    
    def __repr__(self) -> str:
        return f"({self.left} + {self.right})"

class UnionTransform(TransformationNode):
    """A transformation that unions the results of two transformations."""
    def __init__(self, left: TransformationNode, right: TransformationNode):
        self.left = left
        self.right = right
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        left_result = self.left.apply(env)
        right_result = self.right.apply(env)
        return left_result | right_result
    
    def __repr__(self) -> str:
        return f"({self.left} | {self.right})"

class SubtractionTransform(TransformationNode):
    """A transformation that subtracts one transformation result from another."""
    def __init__(self, left: TransformationNode, right: TransformationNode):
        self.left = left
        self.right = right
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        left_result = self.left.apply(env)
        right_result = self.right.apply(env)
        return left_result - right_result
    
    def __repr__(self) -> str:
        return f"({self.left} - {self.right})"

class ComplementTransform(TransformationNode):
    """A transformation that complements the result of another transformation."""
    def __init__(self, inner: TransformationNode):
        self.inner = inner
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        inner_result = self.inner.apply(env)
        return ~inner_result
    
    def __repr__(self) -> str:
        return f"~({self.inner})"

class OptionalTransform(TransformationNode):
    """A transformation that makes the result of another transformation optional."""
    def __init__(self, inner: TransformationNode):
        self.inner = inner
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        inner_result = self.inner.apply(env)
        return inner_result.optional()
    
    def __repr__(self) -> str:
        return f"({self.inner})?"

class KleeneStarTransform(TransformationNode):
    """A transformation that applies Kleene star to the result of another transformation."""
    def __init__(self, inner: TransformationNode):
        self.inner = inner
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        inner_result = self.inner.apply(env)
        return inner_result.kleene_star()
    
    def __repr__(self) -> str:
        return f"({self.inner})*"

class KleenePlusTransform(TransformationNode):
    """A transformation that applies Kleene plus to the result of another transformation."""
    def __init__(self, inner: TransformationNode):
        self.inner = inner
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        inner_result = self.inner.apply(env)
        return inner_result.kleene_plus()
    
    def __repr__(self) -> str:
        return f"({self.inner})+"

class ReverseTransform(TransformationNode):
    """A transformation that reverses the result of another transformation."""
    def __init__(self, inner: TransformationNode):
        self.inner = inner
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        inner_result = self.inner.apply(env)
        return inner_result.reverse()
    
    def __repr__(self) -> str:
        return f"reverse({self.inner})"

# ======== Operations from regular_operator ========

class TranslateCharsTransform(TransformationNode):
    """A transformation that translates characters in the input."""
    def __init__(
        self,
        input_node: TransformationNode,
        source_chars: str,
        target_chars: str,
        invert: bool = False,
        squeeze: bool = False,
        approximate_when_fst_disabled: bool = False,
        line_delimited: bool = False,
        preprocessed: bool = False,
    ):
        self.source_chars = source_chars
        self.target_chars = target_chars
        self.input_node = input_node
        self.invert = invert
        self.squeeze = squeeze
        self.approximate_when_fst_disabled = approximate_when_fst_disabled
        self.line_delimited = line_delimited
        self.preprocessed = preprocessed
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        from stream.config.global_config import CONFIG
        from stream.regular_operator import complement_set, preprocess
        from stream.transducer import compression_FST, product_fst_automaton, translate_to_line_delimited_FST, translation_FST

        input_result = self.input_node.apply(env)

        if self.preprocessed:
            source_chars = self.source_chars
            target_chars = self.target_chars
        else:
            source_chars = preprocess(self.source_chars)
            target_chars = preprocess(self.target_chars)
        if self.invert:
            source_chars = complement_set(source_chars)

        if self.approximate_when_fst_disabled and not CONFIG.get("enable_FST", True):
            return _approximate_translate_chars_without_fst(source_chars, target_chars, self.squeeze, input_result.tainted)

        fst = translate_to_line_delimited_FST(source_chars) if self.line_delimited else translation_FST(source_chars, target_chars)
        output_automaton = product_fst_automaton(fst, input_result.nfa)
        if self.squeeze:
            output_automaton = product_fst_automaton(compression_FST(target_chars), output_automaton)
        return RegularType(
            automaton=output_automaton,
            tainted=input_result.tainted,
        )
    
    def __repr__(self) -> str:
        return f"translate_chars({self.input_node}, '{self.source_chars}', '{self.target_chars}', invert={self.invert}, squeeze={self.squeeze})"


class DeleteCharsTransform(TransformationNode):
    """Delete all characters in a set, represented as translate-match(T, chars, '')."""
    def __init__(
        self,
        input_node: TransformationNode,
        chars: str,
        invert: bool = False,
        approximate_when_fst_disabled: bool = False,
        preprocessed: bool = False,
    ):
        self.input_node = input_node
        self.chars = chars
        self.invert = invert
        self.approximate_when_fst_disabled = approximate_when_fst_disabled
        self.preprocessed = preprocessed

    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        from stream.config.global_config import CONFIG
        from stream.regular_operator import complement_set, preprocess
        from stream.transducer import deletion_FST, product_fst_automaton

        input_result = self.input_node.apply(env)

        chars = self.chars if self.preprocessed else preprocess(self.chars)
        if self.invert:
            chars = complement_set(chars)
        if self.approximate_when_fst_disabled and not CONFIG.get("enable_FST", True):
            return _type_excluding_chars(chars, input_result.tainted)

        fst = deletion_FST(chars)
        return RegularType(
            automaton=product_fst_automaton(fst, input_result.nfa),
            tainted=input_result.tainted,
        )

    def __repr__(self) -> str:
        return f"translate-match({self.input_node}, '[{self.chars}]', '', global=True)"

class FieldSelectTransform(TransformationNode):
    """A transformation that selects fields from the input."""
    def __init__(self, input_node: TransformationNode, delimiter: str, field_indices: str, invert: bool = False):
        self.delimiter = delimiter
        self.field_indices = field_indices
        self.input_node = input_node
        self.invert = invert

    @staticmethod
    def _parse_indices(indices: str) -> Tuple[list[int], bool]:
        if not indices or "${" in indices or "$(" in indices:
            return [], False

        result: list[int] = []
        has_upperbound = True
        no_upperbound_start = float("inf")

        for part in indices.split(","):
            if "-" in part:
                range_parts = part.split("-")
                if len(range_parts) != 2:
                    raise ToolError(f"invalid range format: {part}")
                start, end = range_parts
                if not start:
                    start = "1"
                if not end:
                    has_upperbound = False
                    end = "-1"
                start_int, end_int = int(start), int(end)
                if end_int == -1:
                    no_upperbound_start = min(start_int, no_upperbound_start)
                else:
                    result.extend(range(start_int, end_int + 1))
            else:
                result.append(int(part))

        if not has_upperbound:
            result = [x for x in result if x < no_upperbound_start]
            result.append(int(no_upperbound_start))
        return result, has_upperbound
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        from stream.transducer import (
            correct_cut_field_FST,
            cut_char_FST,
            product_fst_automaton,
        )

        input_result = self.input_node.apply(env)
        indices, has_upperbound = self._parse_indices(self.field_indices)
        if not indices:
            return RegularType(".*", tainted=True)

        if self.invert:
            if not has_upperbound:
                return RegularType(".*", tainted=True)
            selected = set(indices)
            max_index = max(selected)
            indices = [i for i in range(1, max_index + 1) if i not in selected]
            indices.append(max_index + 1)
            has_upperbound = False

        if self.delimiter:
            delimiter = self.delimiter
            while len(delimiter) >= 2 and (
                (delimiter[0] == "(" and delimiter[-1] == ")")
                or (delimiter[0] == "[" and delimiter[-1] == "]")
                or (delimiter[0] == "'" and delimiter[-1] == "'")
                or (delimiter[0] == '"' and delimiter[-1] == '"')
            ):
                delimiter = delimiter[1:-1]
            delimiter = delimiter[-1]
            fst = correct_cut_field_FST(delimiter, indices, has_upperbound)
        else:
            fst = cut_char_FST(indices, has_upperbound)

        return RegularType(
            automaton=product_fst_automaton(fst, input_result.nfa),
            tainted=input_result.tainted,
        )
    
    def __repr__(self) -> str:
        return f"field_select({self.input_node}, '{self.delimiter}', '{self.field_indices}', invert={self.invert})"


class LastFieldTransform(TransformationNode):
    """Select the last field from each input line."""
    def __init__(self, input_node: TransformationNode, delimiter: str):
        self.input_node = input_node
        self.delimiter = delimiter

    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        from stream.transducer import product_fst_automaton, start_regex_replacement_FST

        input_result = self.input_node.apply(env)
        delimiter = self.delimiter
        if delimiter:
            fst = start_regex_replacement_FST(RegularType(f".*{re.escape(delimiter)}").nfa, "")
            return RegularType(
                automaton=product_fst_automaton(fst, input_result.nfa),
                tainted=input_result.tainted,
            )
        return input_result

    def __repr__(self) -> str:
        return f"last-field({self.input_node}, '{self.delimiter}')"

class TranslateMatchTransform(TransformationNode):
    """A transformation that replaces matches in the input."""
    def __init__(
        self,
        input_node: TransformationNode,
        pattern: Union[str, RegularType, TransformationNode],
        replacement: str,
        global_match: bool = False,
        mode: str = "compat",
    ):
        if isinstance(pattern, str):
            pattern = RegexPatternTransform(pattern, mode=mode)
        elif isinstance(pattern, RegularType):
            pattern = ConstantTransform(pattern)
        self.pattern = pattern
        self.replacement = replacement
        self.input_node = input_node
        self.global_match = global_match
        self.mode = mode
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        from stream.regular_operator import translate_match
        
        input_result = self.input_node.apply(env)
        
        # Handle pattern based on its type
        pattern_to_use = self.pattern
        if isinstance(self.pattern, RegexPatternTransform):
            pattern_to_use = self.pattern.pattern
        else:
            pattern_to_use = self.pattern.apply(env)

        try:
            return translate_match(
                input_result,
                pattern_to_use,
                self.replacement,
                self.global_match,
                mode=self.mode,
            )
        except (ToolError, ValueError):
            input_result.tainted = True
            return input_result
    
    def __repr__(self) -> str:
        return f"translate_match({self.input_node}, '{self.pattern}', '{self.replacement}', global_match={self.global_match})"

class LineExtractTransform(TransformationNode):
    """A transformation that extracts lines matching a pattern."""
    def __init__(self, input_node: TransformationNode, pattern: Union[str, RegularType, TransformationNode]):
        if isinstance(pattern, str):
            pattern = RegexPatternTransform(pattern)
        elif isinstance(pattern, RegularType):
            pattern = ConstantTransform(pattern)
        self.pattern = pattern
        self.input_node = input_node
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        from stream.regular_operator import line_extract
        
        input_result = self.input_node.apply(env)
        
        # Handle pattern based on its type
        pattern_to_use = self.pattern
        if isinstance(self.pattern, RegexPatternTransform):
            pattern_to_use = self.pattern.pattern
        else:
            pattern_to_use = self.pattern.apply(env)
            
        return line_extract(input_result, pattern_to_use)
    
    def __repr__(self) -> str:
        return f"line_extract({self.input_node}, '{self.pattern}')"


class HeadLinesTransform(TransformationNode):
    """Select the first n lines of a stream type."""
    def __init__(self, input_node: TransformationNode, line_count: int):
        self.input_node = input_node
        self.line_count = line_count

    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        input_result = self.input_node.apply(env)
        return clone_regular_type(input_result)

    def __repr__(self) -> str:
        return f"head-lines({self.input_node}, {self.line_count})"


class TailLinesTransform(TransformationNode):
    """Select the last n lines of a stream type."""
    def __init__(self, input_node: TransformationNode, line_count: int):
        self.input_node = input_node
        self.line_count = line_count

    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        input_result = self.input_node.apply(env)
        return clone_regular_type(input_result)

    def __repr__(self) -> str:
        return f"tail-lines({self.input_node}, {self.line_count})"


class DefaultIfEmptyStringTransform(TransformationNode):
    """Use a fallback output when the input language is only the empty string."""
    def __init__(self, input_node: TransformationNode, fallback: TransformationNode):
        self.input_node = input_node
        self.fallback = fallback

    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        input_result = self.input_node.apply(env)
        if input_result.is_empty_string():
            return self.fallback.apply(env)
        return input_result

    def __repr__(self) -> str:
        return f"default-if-empty({self.input_node}, {self.fallback})"
    

ALPHA: HoleNode = HoleNode("α")

def regex_ast_to_transform_node(regex_node, hole_transforms: Optional[Mapping[str, TransformationNode]] = None):
    """
    Convert a regex AST node to a transformation AST node.
    
    Args:
        regex_node: A node from the regex AST (from regex_parser module)
    
    Returns:
        TransformationNode: The equivalent transformation AST node
    """
    from stream.regex_parser import (
        Literal, Dot, Concatenate, Repeat, Range, 
        PosixClass, CharacterClass, Intersection, 
        Complement, Union, StartAnchor, EndAnchor, Hole
    )
    
    # Handle leaf nodes
    if hole_transforms is None:
        hole_transforms = {}

    if isinstance(regex_node, Hole):
        if regex_node.name in hole_transforms:
            return hole_transforms[regex_node.name]
        if regex_node.name == "actual_input_type":
            return ALPHA
        return HoleNode(regex_node.name)
    elif isinstance(regex_node, Literal):
        return RegexPatternTransform(regex_node.char)
    elif isinstance(regex_node, Dot):
        return RegexPatternTransform(".")
    elif isinstance(regex_node, StartAnchor):
        return RegexPatternTransform("^")
    elif isinstance(regex_node, EndAnchor):
        return RegexPatternTransform("$")
    
    # Handle non-leaf nodes
    elif isinstance(regex_node, Concatenate):
        if not regex_node.nodes:
            return RegexPatternTransform("")
        result = regex_ast_to_transform_node(regex_node.nodes[0], hole_transforms)
        for node in regex_node.nodes[1:]:
            result = ConcatenateTransform(result, regex_ast_to_transform_node(node, hole_transforms))
        return result
    elif isinstance(regex_node, Union):
        return UnionTransform(
            regex_ast_to_transform_node(regex_node.left, hole_transforms),
            regex_ast_to_transform_node(regex_node.right, hole_transforms)
        )
    elif isinstance(regex_node, Intersection):
        return IntersectionTransform(
            regex_ast_to_transform_node(regex_node.left, hole_transforms),
            regex_ast_to_transform_node(regex_node.right, hole_transforms)
        )
    elif isinstance(regex_node, Complement):
        return ComplementTransform(regex_ast_to_transform_node(regex_node.node, hole_transforms))
    elif isinstance(regex_node, Repeat):
        inner = regex_ast_to_transform_node(regex_node.node, hole_transforms)
        if regex_node.min == 0 and regex_node.max is None:
            return KleeneStarTransform(inner)
        elif regex_node.min == 1 and regex_node.max is None:
            return KleenePlusTransform(inner)
        elif regex_node.min == 0 and regex_node.max == 1:
            return OptionalTransform(inner)
        else:
            # For more complex repeat patterns, convert to regex pattern
            # This is a simplification, as transformation_ast doesn't have a direct equivalent
            from stream.regex_parser import ast_to_regex
            pattern = ast_to_regex(regex_node)
            return RegexPatternTransform(pattern)
    elif isinstance(regex_node, CharacterClass):
        # For character classes, convert to regex pattern
        from stream.regex_parser import ast_to_regex
        pattern = ast_to_regex(regex_node)
        return RegexPatternTransform(pattern)
    elif isinstance(regex_node, Range):
        # For ranges, convert to regex pattern
        pattern = f"[{regex_node.start}-{regex_node.end}]"
        return RegexPatternTransform(pattern)
    elif isinstance(regex_node, PosixClass):
        # For POSIX classes, convert to regex pattern
        pattern = f"[:{regex_node.name}:]"
        return RegexPatternTransform(pattern)
    else:
        raise ValueError(f"Unsupported regex AST node type: {type(regex_node)}")
