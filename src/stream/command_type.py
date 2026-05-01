from typing import Dict, List, Optional, Set, Tuple, Union, Type, Mapping
from stream.regular_type import RegularType
from stream.transformation_ast import (
    TransformationNode, HoleNode, 
    IntersectionTransform, RegexPatternTransform
)

class CommandType:
    """Base class for representing the type of a command."""
    def __init__(self):
        pass
    
    def apply_to_input(self, input_type: RegularType) -> RegularType:
        """Apply this command type to the given input type to produce the output type."""
        raise NotImplementedError("Subclasses must implement apply_to_input")

class SimpleCommandType(CommandType):
    """A simple command type that specifies fixed input, output, and negative constraint."""
    def __init__(self, input_type: RegularType, output_type: RegularType, negative_constraint: Optional[RegularType] = None):
        super().__init__()
        self.input_type = input_type
        self.negative_constraint = negative_constraint
        self.output_type = output_type
    
    def apply_to_input(self, input_type: RegularType) -> RegularType:
        # For simple command types, the output is always the same regardless of input
        return self.output_type
    
    def __repr__(self) -> str:
        if self.negative_constraint is not None:
            return f"({self.input_type}, {self.negative_constraint}) -> {self.output_type}"
        else:
            return f"{self.input_type} -> {self.output_type}"

class PolymorphicCommandType(CommandType):
    """
    A polymorphic command type that can adapt based on the input type.
    
    This represents the type: ∀α ⊆ Bound, α ⊄ NegativeConstraint. α -> TransformAST
    
    Where:
    - α is a type parameter
    - Bound is an optional upper bound on the type parameter
    - NegativeConstraint is an optional negative constraint on the type parameter
    - TransformAST is an AST expression that can reference α and compute the output type
    """
    def __init__(self, 
                 transformation: TransformationNode,
                 bound: Optional[RegularType] = None, 
                 negative_constraint: Optional[RegularType] = None):
        super().__init__()
        self.bound = bound  # Upper bound on the type parameter
        self.negative_constraint = negative_constraint  # Negative constraint on the type parameter
        self.transformation = transformation
    
    def apply_to_input(self, input_type: RegularType) -> RegularType:
        env = {"α": input_type}
        return self.transformation.apply(env)
    
    def __repr__(self) -> str:
        bound_str = f"[α ⊆ {self.bound}]" if self.bound else ""
        negative_constraint_str = f"[α ⊄ {self.negative_constraint}]" if self.negative_constraint else ""
        return f"∀α{bound_str}{negative_constraint_str}. α -> {self.transformation}"