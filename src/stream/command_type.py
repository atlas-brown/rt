from dataclasses import dataclass
from typing import Any, Callable, Optional
from stream.regular_type import RegularType
from stream.transformation_ast import (
    clone_regular_type,
    TransformationNode,
)

@dataclass
class CommandTypeResult:
    output_type: RegularType
    backward_func: Optional[Callable[[Any], Any]] = None
    self_contained: Optional[bool] = None


class CommandType:
    """Base class for representing the type of a command."""
    def __init__(
        self,
        backward_func: Optional[Callable[[Any], Any]] = None,
        self_contained: Optional[bool] = None,
    ):
        self.backward_func = backward_func
        self.self_contained = self_contained
    
    def apply_to_input(self, input_type: RegularType) -> CommandTypeResult:
        """Apply this command type to the given input type to produce the output type."""
        raise NotImplementedError("Subclasses must implement apply_to_input")

    def _coerce_result(self, result: Any) -> CommandTypeResult:
        if isinstance(result, CommandTypeResult):
            return result
        if isinstance(result, RegularType):
            return CommandTypeResult(result, self.backward_func, self.self_contained)
        if hasattr(result, "output_type"):
            return CommandTypeResult(
                result.output_type,
                getattr(result, "backward_func", self.backward_func),
                getattr(result, "self_contained", self.self_contained),
            )
        raise TypeError(f"Command type transformation returned unsupported result {type(result)}")

class SimpleCommandType(CommandType):
    """A simple command type that specifies fixed input, output, and negative constraint."""
    def __init__(
        self,
        input_type: RegularType,
        output_type: RegularType,
        negative_constraint: Optional[RegularType] = None,
        backward_func: Optional[Callable[[Any], Any]] = None,
        self_contained: Optional[bool] = None,
    ):
        super().__init__(backward_func=backward_func, self_contained=self_contained)
        self.input_type = input_type
        self.negative_constraint = negative_constraint
        self.output_type = output_type
    
    def apply_to_input(self, input_type: RegularType) -> CommandTypeResult:
        # For simple command types, the output is always the same regardless of input
        return CommandTypeResult(
            clone_regular_type(self.output_type),
            self.backward_func,
            self.self_contained,
        )
    
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
                 negative_constraint: Optional[RegularType] = None,
                 backward_func: Optional[Callable[[Any], Any]] = None,
                 self_contained: Optional[bool] = None,
                 normalize_input_to_line: Optional[bool] = None,
                 output_tainted: Optional[bool] = None):
        super().__init__(backward_func=backward_func, self_contained=self_contained)
        self.bound = bound  # Upper bound on the type parameter
        self.negative_constraint = negative_constraint  # Negative constraint on the type parameter
        self.transformation = transformation
        self.normalize_input_to_line = normalize_input_to_line
        self.output_tainted = output_tainted
    
    def apply_to_input(self, input_type: RegularType) -> CommandTypeResult:
        actual_input = input_type
        if self.normalize_input_to_line is True and input_type.repr_mode == "stream":
            actual_input = input_type.to_line_based_repr()
        env = {"α": actual_input, "actual_input_type": actual_input}
        result = self._coerce_result(self.transformation.apply(env))
        if self.output_tainted is not None:
            result.output_type.tainted = self.output_tainted
        return result
    
    def __repr__(self) -> str:
        bound_str = f"[α ⊆ {self.bound}]" if self.bound else ""
        negative_constraint_str = f"[α ⊄ {self.negative_constraint}]" if self.negative_constraint else ""
        return f"∀α{bound_str}{negative_constraint_str}. α -> {self.transformation}"
