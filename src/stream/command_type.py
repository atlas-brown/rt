from typing import Optional

from stream.regular_type import RegularType
from stream.transformation_ast import (
    clone_regular_type,
    TransformationNode,
)


class CommandType:
    """Base class for representing the type of a command."""
    def __init__(
        self,
        input_type: Optional[RegularType] = None,
        no_input_type: Optional[RegularType] = None,
        self_contained: Optional[bool] = None,
    ):
        self.input_type = input_type if input_type is not None else RegularType(".*")
        self.no_input_type = no_input_type
        self.self_contained = self_contained

    def set_input_constraints(
        self,
        input_type: RegularType,
        no_input_type: Optional[RegularType],
    ) -> None:
        self.input_type = input_type
        self.no_input_type = no_input_type

    def apply_to_input(self, input_type: RegularType) -> RegularType:
        """Apply this command type to the given input type to produce the output type."""
        raise NotImplementedError("Subclasses must implement apply_to_input")


class SimpleCommandType(CommandType):
    """A simple command type that specifies fixed input, output, and negative constraint."""
    def __init__(
        self,
        input_type: RegularType,
        output_type: RegularType,
        negative_constraint: Optional[RegularType] = None,
        self_contained: Optional[bool] = None,
        no_input_type: Optional[RegularType] = None,
    ):
        if no_input_type is None:
            no_input_type = negative_constraint
        super().__init__(
            input_type=input_type,
            no_input_type=no_input_type,
            self_contained=self_contained,
        )
        self.output_type = output_type

    def apply_to_input(self, input_type: RegularType) -> RegularType:
        return clone_regular_type(self.output_type)

    def __repr__(self) -> str:
        if self.no_input_type is not None:
            return f"({self.input_type}, {self.no_input_type}) -> {self.output_type}"
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
                 self_contained: Optional[bool] = None,
                 output_tainted: Optional[bool] = None,
                 input_type: Optional[RegularType] = None,
                 no_input_type: Optional[RegularType] = None):
        if input_type is None:
            input_type = bound
        if no_input_type is None:
            no_input_type = negative_constraint
        super().__init__(
            input_type=input_type,
            no_input_type=no_input_type,
            self_contained=self_contained,
        )
        self.transformation = transformation
        self.output_tainted = output_tainted

    def apply_to_input(self, input_type: RegularType) -> RegularType:
        env = {"α": input_type, "actual_input_type": input_type}
        result = self.transformation.apply(env)
        if self.output_tainted is not None:
            result.tainted = self.output_tainted
        return result

    def __repr__(self) -> str:
        bound_str = f"[α ⊆ {self.input_type}]" if self.input_type else ""
        negative_constraint_str = f"[α ⊄ {self.no_input_type}]" if self.no_input_type else ""
        return f"∀α{bound_str}{negative_constraint_str}. α -> {self.transformation}"
