from typing import Dict, List, Optional, Set, Tuple, Union, Any, Mapping
from stream.regular_type import RegularType
import re

from stream.tool_error import ToolError

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
        return self.output_type
    
    def __repr__(self) -> str:
        return f"Constant({self.output_type})"

class RegexPatternTransform(TransformationNode):
    """A transformation that creates a RegularType from a regex pattern."""
    def __init__(self, pattern: str):
        self.pattern = pattern
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        return RegularType(self.pattern)
    
    def __repr__(self) -> str:
        return f"RegexPattern('{self.pattern}')"

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
    def __init__(self, input_node: TransformationNode, source_chars: str, target_chars: str, invert: bool = False, squeeze: bool = False):
        self.source_chars = source_chars
        self.target_chars = target_chars
        self.input_node = input_node
        self.invert = invert
        self.squeeze = squeeze
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        from stream.regular_operator import translate_chars
        input_result = self.input_node.apply(env)
        return translate_chars(input_result, self.source_chars, self.target_chars, self.invert, self.squeeze)
    
    def __repr__(self) -> str:
        return f"translate_chars({self.input_node}, '{self.source_chars}', '{self.target_chars}', invert={self.invert}, squeeze={self.squeeze})"

class FieldSelectTransform(TransformationNode):
    """A transformation that selects fields from the input."""
    def __init__(self, input_node: TransformationNode, delimiter: str, field_indices: str, invert: bool = False):
        self.delimiter = delimiter
        self.field_indices = field_indices
        self.input_node = input_node
        self.invert = invert
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        from stream.regular_operator import field_select
        input_result = self.input_node.apply(env)
        return field_select(input_result, self.delimiter, self.field_indices, self.invert)
    
    def __repr__(self) -> str:
        return f"field_select({self.input_node}, '{self.delimiter}', '{self.field_indices}', invert={self.invert})"

class TranslateMatchTransform(TransformationNode):
    """A transformation that replaces matches in the input."""
    def __init__(self, input_node: TransformationNode, pattern: Union[str, RegularType, TransformationNode], replacement: str, global_match: bool = False):
        if isinstance(pattern, str):
            pattern = RegexPatternTransform(pattern)
        elif isinstance(pattern, RegularType):
            pattern = ConstantTransform(pattern)
        self.pattern = pattern
        self.replacement = replacement
        self.input_node = input_node
        self.global_match = global_match
        
    def apply(self, env: Mapping[str, RegularType]) -> RegularType:
        from stream.regular_operator import translate_match
        
        input_result = self.input_node.apply(env)
        
        # Handle pattern based on its type
        pattern_to_use = self.pattern
        if isinstance(self.pattern, RegexPatternTransform):
            pattern_to_use = self.pattern.pattern
        else:
            pattern_to_use = self.pattern.apply(env)
        
            
        return translate_match(input_result, pattern_to_use, self.replacement, self.global_match)
    
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
    

ALPHA: HoleNode = HoleNode("α")

# # ======== Naming conventions and convenience functions ========

# # Define common holes
# alpha = HoleNode("α")
# beta = HoleNode("β")
# gamma = HoleNode("γ")
# input_hole = HoleNode("input")

# # Convenience function for creating a RegexPattern
# def regex(pattern: str) -> RegexPatternTransform:
#     return RegexPatternTransform(pattern)

# # Convenience function for intersecting with a pattern
# def intersect_with_pattern(node: TransformationNode, pattern: str) -> IntersectionTransform:
#     return IntersectionTransform(node, RegexPatternTransform(pattern))

# # Convenience function for applying a transformation with an input
# def apply_transform(transform: TransformationNode, input_type: RegularType) -> RegularType:
#     return transform.apply({"input": input_type, "α": input_type})

# # ======== AST Builder Utility ========

# def build_transform_from_dict(transform_dict: Dict[str, Any]) -> TransformationNode:
#     """Build a transformation AST from a dictionary representation."""
#     transform_type = transform_dict.get('type')
    
#     if transform_type == 'identity':
#         return IdentityTransform()
    
#     elif transform_type == 'hole':
#         return HoleNode(transform_dict.get('name', 'α'))
    
#     elif transform_type == 'constant':
#         return ConstantTransform(RegularType(transform_dict['pattern']))
    
#     elif transform_type == 'regex_pattern':
#         return RegexPatternTransform(transform_dict['pattern'])
    
#     elif transform_type == 'intersection':
#         left = build_transform_from_dict(transform_dict['left'])
#         right = build_transform_from_dict(transform_dict['right'])
#         return IntersectionTransform(left, right)
    
#     elif transform_type == 'concatenate':
#         left = build_transform_from_dict(transform_dict['left'])
#         right = build_transform_from_dict(transform_dict['right'])
#         return ConcatenateTransform(left, right)
    
#     elif transform_type == 'union':
#         left = build_transform_from_dict(transform_dict['left'])
#         right = build_transform_from_dict(transform_dict['right'])
#         return UnionTransform(left, right)
    
#     elif transform_type == 'subtraction':
#         left = build_transform_from_dict(transform_dict['left'])
#         right = build_transform_from_dict(transform_dict['right'])
#         return SubtractionTransform(left, right)
    
#     elif transform_type == 'complement':
#         inner = build_transform_from_dict(transform_dict['inner'])
#         return ComplementTransform(inner)
    
#     elif transform_type == 'optional':
#         inner = build_transform_from_dict(transform_dict['inner'])
#         return OptionalTransform(inner)
    
#     elif transform_type == 'kleene_star':
#         inner = build_transform_from_dict(transform_dict['inner'])
#         return KleeneStarTransform(inner)
    
#     elif transform_type == 'kleene_plus':
#         inner = build_transform_from_dict(transform_dict['inner'])
#         return KleenePlusTransform(inner)
    
#     elif transform_type == 'reverse':
#         inner = build_transform_from_dict(transform_dict['inner'])
#         return ReverseTransform(inner)
    
#     elif transform_type == 'translate_chars':
#         input_node = build_transform_from_dict(transform_dict.get('input', {'type': 'hole', 'name': 'input'}))
#         return TranslateCharsTransform(
#             transform_dict['source_chars'],
#             transform_dict['target_chars'],
#             input_node,
#             transform_dict.get('invert', False),
#             transform_dict.get('squeeze', False)
#         )
    
#     elif transform_type == 'field_select':
#         input_node = build_transform_from_dict(transform_dict.get('input', {'type': 'hole', 'name': 'input'}))
#         return FieldSelectTransform(
#             transform_dict['delimiter'],
#             transform_dict['field_indices'],
#             input_node,
#             transform_dict.get('invert', False)
#         )
    
#     elif transform_type == 'translate_match':
#         pattern = transform_dict['pattern']
#         if isinstance(pattern, dict):
#             pattern = build_transform_from_dict(pattern)
#         elif isinstance(pattern, str) and pattern.startswith('/') and pattern.endswith('/'):
#             pattern = RegexPatternTransform(pattern[1:-1])
            
#         input_node = build_transform_from_dict(transform_dict.get('input', {'type': 'hole', 'name': 'input'}))
        
#         return TranslateMatchTransform(
#             pattern,
#             transform_dict['replacement'],
#             input_node,
#             transform_dict.get('global_match', False)
#         )
    
#     elif transform_type == 'line_extract':
#         pattern = transform_dict['pattern']
#         if isinstance(pattern, dict):
#             pattern = build_transform_from_dict(pattern)
#         elif isinstance(pattern, str) and pattern.startswith('/') and pattern.endswith('/'):
#             pattern = RegexPatternTransform(pattern[1:-1])
            
#         input_node = build_transform_from_dict(transform_dict.get('input', {'type': 'hole', 'name': 'input'}))
        
#         return LineExtractTransform(pattern, input_node)
    
#     elif transform_type == 'composite':
#         transforms = [build_transform_from_dict(t) for t in transform_dict['transforms']]
#         input_node = build_transform_from_dict(transform_dict.get('input', {'type': 'hole', 'name': 'input'}))
#         return CompositeTransform(transforms, input_node)
    
#     else:
#         raise ValueError(f"Unknown transformation type: {transform_type}")

def regex_ast_to_transform_node(regex_node):
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
    if isinstance(regex_node, Hole):
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
        result = regex_ast_to_transform_node(regex_node.nodes[0])
        for node in regex_node.nodes[1:]:
            result = ConcatenateTransform(result, regex_ast_to_transform_node(node))
        return result
    elif isinstance(regex_node, Union):
        return UnionTransform(
            regex_ast_to_transform_node(regex_node.left),
            regex_ast_to_transform_node(regex_node.right)
        )
    elif isinstance(regex_node, Intersection):
        return IntersectionTransform(
            regex_ast_to_transform_node(regex_node.left),
            regex_ast_to_transform_node(regex_node.right)
        )
    elif isinstance(regex_node, Complement):
        return ComplementTransform(regex_ast_to_transform_node(regex_node.node))
    elif isinstance(regex_node, Repeat):
        inner = regex_ast_to_transform_node(regex_node.node)
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