from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union, Iterable

from stream.special_signatures._awk.parser import (
    AwkProgram,
    AwkRule,
    AwkAction,
    AwkStatement,
    PrintStatement,
    PrintfStatement,
    AssignmentStatement,
    IncrementStatement,
    IfStatement,
    ForStatement,
    AwkExpression,
    BinaryOperation,
    UnaryOperation,
    FieldReference,
    Variable,
    ArrayAccess,
    StringLiteral,
    NumberLiteral,
    RegexLiteral,
    FunctionCall,
    ConditionalExpression,
    RegexPattern,
    ExpressionPattern,
)


class SimpleTypeName(Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOL = "bool"


NUMERIC_ORDER: List[SimpleTypeName] = [
    SimpleTypeName.INT,
    SimpleTypeName.FLOAT,
    SimpleTypeName.STRING,
]


@dataclass(frozen=True)
class SimpleType:
    name: SimpleTypeName

    def __str__(self) -> str:
        return self.name.value


@dataclass(frozen=True)
class ArrayType:
    element: SimpleType

    def __str__(self) -> str:
        return f"array[{self.element}]"


TypeLike = Union[SimpleType, ArrayType]


def is_numeric(t: SimpleTypeName) -> bool:
    return t in (SimpleTypeName.INT, SimpleTypeName.FLOAT)


def order_index(t: SimpleTypeName) -> int:
    if t == SimpleTypeName.INT:
        return 0
    if t == SimpleTypeName.FLOAT:
        return 1
    if t == SimpleTypeName.STRING:
        return 2
    raise ValueError("BOOL is not ordered on the numeric-string chain")


def lub_simple(a: SimpleTypeName, b: SimpleTypeName) -> SimpleTypeName:
    if a == b:
        return a
    if a == SimpleTypeName.BOOL or b == SimpleTypeName.BOOL:
        return SimpleTypeName.STRING
    return NUMERIC_ORDER[max(order_index(a), order_index(b))]


@dataclass
class VarConstraints:
    hard_min_chain: Optional[SimpleTypeName] = None
    hard_exact: Optional[SimpleTypeName] = None
    soft_preference: Optional[SimpleTypeName] = None
    notes: List[str] = field(default_factory=list)

    def add_hard_min(self, t: SimpleTypeName, note: str) -> None:
        if self.hard_min_chain is None:
            self.hard_min_chain = t
        else:
            if self.hard_min_chain == SimpleTypeName.BOOL and t != SimpleTypeName.BOOL:
                self.hard_min_chain = t
            elif t != SimpleTypeName.BOOL and self.hard_min_chain != SimpleTypeName.BOOL:
                self.hard_min_chain = lub_simple(self.hard_min_chain, t)
        self.notes.append(f"hard_min {t.value}: {note}")

    def add_hard_exact(self, t: SimpleTypeName, note: str) -> None:
        self.hard_exact = t
        self.notes.append(f"hard_exact {t.value}: {note}")

    def add_soft_pref(self, t: SimpleTypeName, note: str) -> None:
        self.soft_preference = t
        self.notes.append(f"soft_preference {t.value}: {note}")


@dataclass
class VarInfo:
    name: str
    is_array: bool = False
    simple: VarConstraints = field(default_factory=VarConstraints)
    element: VarConstraints = field(default_factory=VarConstraints)
    usage_conflicts: List[str] = field(default_factory=list)


class TypeEnv:
    def __init__(self) -> None:
        self.vars: Dict[str, VarInfo] = {}

    def ensure_simple(self, name: str) -> VarInfo:
        info = self.vars.get(name)
        if info is None:
            info = VarInfo(name=name)
            self.vars[name] = info
        else:
            if info.is_array:
                info.usage_conflicts.append("used as simple but previously as array")
        return info

    def ensure_array(self, name: str) -> VarInfo:
        info = self.vars.get(name)
        if info is None:
            info = VarInfo(name=name, is_array=True)
            self.vars[name] = info
        else:
            if not info.is_array:
                info.usage_conflicts.append("used as array but previously as simple")
                info.is_array = True
        return info

    def ensure_field(self, field_key: str) -> VarInfo:
        return self.ensure_simple(f"FIELD[{field_key}]")

    def items(self) -> Iterable[Tuple[str, VarInfo]]:
        return self.vars.items()


@dataclass
class InferenceResult:
    resolved: Dict[str, TypeLike]
    diagnostics: List[str]


class AwkTypeChecker:
    def __init__(self) -> None:
        self.env = TypeEnv()
        self.diagnostics: List[str] = []

    def type_program(self, program: AwkProgram) -> InferenceResult:
        for rule in program.rules:
            self._type_rule(rule)
        resolved = self._solve()
        return InferenceResult(resolved=resolved, diagnostics=self.diagnostics)

    def _type_rule(self, rule: AwkRule) -> None:
        if isinstance(rule.pattern, ExpressionPattern):
            self._type_expr(rule.pattern.expression)

        if rule.action:
            for stmt in rule.action.statements:
                self._type_stmt(stmt)

    def _type_stmt(self, stmt: AwkStatement) -> None:
        if isinstance(stmt, PrintStatement):
            for e in stmt.expressions:
                self._type_expr(e)
            return

        if isinstance(stmt, PrintfStatement):
            self._type_printf(stmt)
            return

        if isinstance(stmt, AssignmentStatement):
            self._type_assignment(stmt)
            return

        if isinstance(stmt, IncrementStatement):
            self._type_increment(stmt)
            return

        if isinstance(stmt, IfStatement):
            self._type_expr(stmt.condition)
            for s in stmt.then_action.statements:
                self._type_stmt(s)
            if stmt.else_action:
                for s in stmt.else_action.statements:
                    self._type_stmt(s)
            return

        if isinstance(stmt, ForStatement):
            key_info = self.env.ensure_simple(stmt.variable)
            key_info.simple.add_hard_min(SimpleTypeName.STRING, "for (k in arr) key coerced to string")
            self._require_array(stmt.iterable, "for-in iterable must be array")
            for s in stmt.action.statements:
                self._type_stmt(s)
            return

        return

    def _type_assignment(self, stmt: AssignmentStatement) -> None:
        value_type = self._type_expr(stmt.value)
        target_expr = stmt.target
        op = stmt.operator

        if isinstance(target_expr, ArrayAccess):
            arr = target_expr.array
            arr_name = self._extract_var_name(arr)
            if not arr_name:
                self._type_expr(arr)  # still traverse
            info = self.env.ensure_array(arr_name or "<unknown array>")
            self._type_expr(target_expr.index)
            info.element.add_hard_min(self._to_simple_min(value_type), f"{arr_name}[..] {op} value")
            if op in ("+=", "-=", "*=", "/=", "%="):
                min_needed = SimpleTypeName.FLOAT if op == "/=" else SimpleTypeName.INT
                info.element.add_hard_min(min_needed, f"{arr_name}[..] {op} compound assignment numeric")
            return

        if isinstance(target_expr, Variable):
            name = target_expr.name
            info = self.env.ensure_simple(name)
            info.simple.add_hard_min(self._to_simple_min(value_type), f"{name} {op} value")
            if op in ("+=", "-=", "*=", "/=", "%="):
                min_needed = SimpleTypeName.FLOAT if op == "/=" else SimpleTypeName.INT
                info.simple.add_hard_min(min_needed, f"{name} {op} compound assignment numeric")
            return

        if isinstance(target_expr, FieldReference):
            field_key = self._field_key(target_expr)
            info = self.env.ensure_field(field_key)
            info.simple.add_hard_min(self._to_simple_min(value_type), f"{field_key} {op} value")
            return

        self._type_expr(target_expr)

    def _type_increment(self, stmt: IncrementStatement) -> None:
        # var++ or ++var
        var_expr = stmt.variable
        if isinstance(var_expr, ArrayAccess):
            arr = var_expr.array
            arr_name = self._extract_var_name(arr)
            if not arr_name:
                self._type_expr(arr)
            info = self.env.ensure_array(arr_name or "<unknown array>")
            self._type_expr(var_expr.index)
            # Hard numeric requirement, but soft-prefer INT for counters
            info.element.add_hard_min(SimpleTypeName.INT, f"{arr_name}[..]{stmt.operator} numeric")
            info.element.add_soft_pref(SimpleTypeName.INT, f"{arr_name}[..]{stmt.operator} counter preference")
            return

        if isinstance(var_expr, Variable):
            name = var_expr.name
            info = self.env.ensure_simple(name)
            # Numeric with preference for INT, because the initial value is 0
            info.simple.add_hard_min(SimpleTypeName.INT, f"{name}{stmt.operator} numeric increment")
            info.simple.add_soft_pref(SimpleTypeName.INT, f"{name}{stmt.operator} counter preference")
            return

        if isinstance(var_expr, FieldReference):
            field_key = self._field_key(var_expr)
            info = self.env.ensure_field(field_key)
            info.simple.add_hard_min(SimpleTypeName.INT, f"{field_key}{stmt.operator} numeric increment")
            info.simple.add_soft_pref(SimpleTypeName.INT, f"{field_key}{stmt.operator} counter preference")
            return

        self._type_expr(var_expr)

    def _type_printf(self, stmt: PrintfStatement) -> None:
        fmt_type = self._type_expr(stmt.format_string)
        if isinstance(stmt.format_string, StringLiteral):
            specs = self._parse_format_specifiers(stmt.format_string.value)
            for i, spec in enumerate(specs):
                if i >= len(stmt.arguments):
                    break
                arg = stmt.arguments[i]
                self._apply_format_constraint(arg, spec)
            for arg in stmt.arguments:
                self._type_expr(arg)
        else:
            for arg in stmt.arguments:
                self._type_expr(arg)

    def _apply_format_constraint(self, arg: AwkExpression, spec: str) -> None:
        spec = spec.lower()
        required: Optional[SimpleTypeName] = None
        if spec in ("d", "i", "o", "u", "x"):
            required = SimpleTypeName.INT
        elif spec in ("f", "e", "g", "a"):
            required = SimpleTypeName.FLOAT
        elif spec in ("s",):
            required = SimpleTypeName.STRING
        elif spec in ("c",):
            required = SimpleTypeName.INT

        if required is None:
            self._type_expr(arg)
            return

        if isinstance(arg, Variable):
            info = self.env.ensure_simple(arg.name)
            info.simple.add_hard_exact(required, f"printf % {spec}")
            return
        if isinstance(arg, FieldReference):
            field_key = self._field_key(arg)
            info = self.env.ensure_field(field_key)
            info.simple.add_hard_exact(required, f"printf % {spec}")
            return
        if isinstance(arg, ArrayAccess):
            arr_name = self._extract_var_name(arg.array)
            if not arr_name:
                self._type_expr(arg.array)
            info = self.env.ensure_array(arr_name or "<unknown array>")
            self._type_expr(arg.index)
            info.element.add_hard_exact(required, f"printf % {spec} on element")
            return

        self._type_expr(arg)

    def _type_expr(self, expr: AwkExpression) -> SimpleType:
        if isinstance(expr, NumberLiteral):
            if isinstance(expr.value, int):
                return SimpleType(SimpleTypeName.INT)
            return SimpleType(SimpleTypeName.FLOAT)

        if isinstance(expr, StringLiteral):
            return SimpleType(SimpleTypeName.STRING)

        if isinstance(expr, RegexLiteral):
            return SimpleType(SimpleTypeName.STRING)

        if isinstance(expr, FieldReference):
            field_key = self._field_key(expr)
            self.env.ensure_field(field_key)
            return SimpleType(SimpleTypeName.STRING)

        if isinstance(expr, Variable):
            self.env.ensure_simple(expr.name)
            return SimpleType(SimpleTypeName.STRING)

        if isinstance(expr, ArrayAccess):
            arr_name = self._extract_var_name(expr.array)
            if not arr_name:
                self._type_expr(expr.array)
            info = self.env.ensure_array(arr_name or "<unknown array>")
            self._type_expr(expr.index)
            return SimpleType(SimpleTypeName.STRING)

        if isinstance(expr, FunctionCall):
            return self._type_function_call(expr)

        if isinstance(expr, ConditionalExpression):
            _ = self._type_expr(expr.condition)
            t_true = self._type_expr(expr.true_expr).name
            t_false = self._type_expr(expr.false_expr).name
            return SimpleType(lub_simple(t_true, t_false))

        if isinstance(expr, UnaryOperation):
            if expr.operator in ("+", "-"):
                self._require_numeric(expr.operand, at_least_float=True, note=f"unary {expr.operator}")
                return SimpleType(SimpleTypeName.FLOAT)
            if expr.operator == "!":
                # boolean result
                return SimpleType(SimpleTypeName.BOOL)
            if expr.operator in ("++", "--"):
                self._require_counter_like(expr.operand, note=f"prefix {expr.operator}")
                return SimpleType(SimpleTypeName.INT)
            return SimpleType(SimpleTypeName.STRING)

        if isinstance(expr, BinaryOperation):
            op = expr.operator
            if op in ("+", "-", "*", "/", "%"):
                at_least_float = (op == "/")
                self._require_numeric(expr.left, at_least_float=at_least_float, note=f"binary {op} left")
                self._require_numeric(expr.right, at_least_float=at_least_float, note=f"binary {op} right")
                if op == "/":
                    return SimpleType(SimpleTypeName.FLOAT)
                return SimpleType(SimpleTypeName.FLOAT)
            if op in ("~", "!~"):
                self._coerce_to_string(expr.left, note=f"{op} left")
                _ = self._type_expr(expr.right)
                return SimpleType(SimpleTypeName.BOOL)
            if op in ("<", "<=", ">", ">=", "==", "!="):
                self._type_expr(expr.left)
                self._type_expr(expr.right)
                return SimpleType(SimpleTypeName.BOOL)
            if op == "in":
                self._require_array(expr.right, note="x in arr requires array")
                self._coerce_to_string(expr.left, note="x in arr coerced to string")
                return SimpleType(SimpleTypeName.BOOL)
            return SimpleType(SimpleTypeName.STRING)

        return SimpleType(SimpleTypeName.STRING)

    def _type_function_call(self, call: FunctionCall) -> SimpleType:
        name = call.function_name
        lname = name.lower()
        if lname == "length":
            if call.arguments:
                self._coerce_to_string(call.arguments[0], note="length() arg")
            return SimpleType(SimpleTypeName.INT)
        if lname == "sqrt":
            if call.arguments:
                self._require_numeric(call.arguments[0], at_least_float=True, note="sqrt() arg")
            return SimpleType(SimpleTypeName.FLOAT)
        if lname == "int":
            if call.arguments:
                self._require_numeric(call.arguments[0], at_least_float=False, note="int() arg numeric")
            return SimpleType(SimpleTypeName.INT)
        if lname == "sprintf":
            if call.arguments:
                fmt_expr = call.arguments[0]
                if isinstance(fmt_expr, StringLiteral):
                    specs = self._parse_format_specifiers(fmt_expr.value)
                    for i, spec in enumerate(specs):
                        idx = i + 1
                        if idx >= len(call.arguments):
                            break
                        self._apply_format_constraint(call.arguments[idx], spec)
                else:
                    for a in call.arguments[1:]:
                        self._type_expr(a)
            return SimpleType(SimpleTypeName.STRING)
        for a in call.arguments:
            self._type_expr(a)
        return SimpleType(SimpleTypeName.STRING)

    def _require_array(self, expr: AwkExpression, note: str) -> None:
        if isinstance(expr, Variable):
            self.env.ensure_array(expr.name)
            return
        if isinstance(expr, ArrayAccess):
            name = self._extract_var_name(expr.array)
            if not name:
                self._type_expr(expr.array)
            self.env.ensure_array(name or "<unknown array>")
            self._type_expr(expr.index)
            return
        self._type_expr(expr)

    def _coerce_to_string(self, expr: AwkExpression, note: str) -> None:
        if isinstance(expr, Variable):
            info = self.env.ensure_simple(expr.name)
            info.simple.add_hard_min(SimpleTypeName.STRING, note)
            return
        if isinstance(expr, FieldReference):
            field_key = self._field_key(expr)
            info = self.env.ensure_field(field_key)
            info.simple.add_hard_min(SimpleTypeName.STRING, note)
            return
        if isinstance(expr, ArrayAccess):
            name = self._extract_var_name(expr.array)
            if not name:
                self._type_expr(expr.array)
            info = self.env.ensure_array(name or "<unknown array>")
            self._type_expr(expr.index)
            info.element.add_hard_min(SimpleTypeName.STRING, note)
            return
        self._type_expr(expr)

    def _require_numeric(self, expr: AwkExpression, at_least_float: bool, note: str) -> None:
        needed = SimpleTypeName.FLOAT if at_least_float else SimpleTypeName.INT
        if isinstance(expr, UnaryOperation) and expr.operator in ("++", "--"):
            self._require_numeric(expr.operand, at_least_float=at_least_float, note=note + " via ++/--")
            return
        if isinstance(expr, Variable):
            info = self.env.ensure_simple(expr.name)
            info.simple.add_hard_min(needed, note)
            return
        if isinstance(expr, FieldReference):
            field_key = self._field_key(expr)
            info = self.env.ensure_field(field_key)
            info.simple.add_hard_min(needed, note)
            return
        if isinstance(expr, ArrayAccess):
            arr_name = self._extract_var_name(expr.array)
            if not arr_name:
                self._type_expr(expr.array)
            info = self.env.ensure_array(arr_name or "<unknown array>")
            self._type_expr(expr.index)
            info.element.add_hard_min(needed, note)
            return
        # Fallback traverse
        self._type_expr(expr)

    def _require_counter_like(self, expr: AwkExpression, note: str) -> None:
        if isinstance(expr, Variable):
            info = self.env.ensure_simple(expr.name)
            info.simple.add_hard_min(SimpleTypeName.INT, note)
            info.simple.add_soft_pref(SimpleTypeName.INT, note + " preference")
            return
        if isinstance(expr, FieldReference):
            field_key = self._field_key(expr)
            info = self.env.ensure_field(field_key)
            info.simple.add_hard_min(SimpleTypeName.INT, note)
            info.simple.add_soft_pref(SimpleTypeName.INT, note + " preference")
            return
        if isinstance(expr, ArrayAccess):
            arr_name = self._extract_var_name(expr.array)
            if not arr_name:
                self._type_expr(expr.array)
            info = self.env.ensure_array(arr_name or "<unknown array>")
            self._type_expr(expr.index)
            info.element.add_hard_min(SimpleTypeName.INT, note)
            info.element.add_soft_pref(SimpleTypeName.INT, note + " preference")
            return
        self._type_expr(expr)

    def _field_key(self, field: FieldReference) -> str:
        # $1 -> FIELD[1], $NF -> FIELD[NF]
        idx_expr = field.index
        if isinstance(idx_expr, NumberLiteral):
            return str(idx_expr.value)
        if isinstance(idx_expr, Variable):
            return idx_expr.name
        return "?"

    def _extract_var_name(self, expr: AwkExpression) -> Optional[str]:
        if isinstance(expr, Variable):
            return expr.name
        return None

    def _to_simple_min(self, t: SimpleType) -> SimpleTypeName:
        return t.name

    def _parse_format_specifiers(self, fmt: str) -> List[str]:
        specs: List[str] = []
        i = 0
        n = len(fmt)
        while i < n:
            if fmt[i] != '%':
                i += 1
                continue
            i += 1
            if i < n and fmt[i] == '%':
                i += 1
                continue
            while i < n and fmt[i] in ' #+0-':
                i += 1
            while i < n and fmt[i].isdigit():
                i += 1
            if i < n and fmt[i] == '.':
                i += 1
                while i < n and fmt[i].isdigit():
                    i += 1
            while i < n and fmt[i] in 'hlL':
                i += 1
            if i < n:
                conv = fmt[i]
                specs.append(conv)
                i += 1
        return specs

    def _solve(self) -> Dict[str, TypeLike]:
        resolved: Dict[str, TypeLike] = {}
        for name, info in self.env.items():
            if info.usage_conflicts:
                self.diagnostics.append(f"Conflict for {name}: {'; '.join(info.usage_conflicts)}")
            if info.is_array:
                elem_type = self._resolve_simple_constraints(info.element, name, is_element=True)
                resolved[name] = ArrayType(SimpleType(elem_type))
            else:
                simple_type = self._resolve_simple_constraints(info.simple, name, is_element=False)
                resolved[name] = SimpleType(simple_type)
        return resolved

    def _resolve_simple_constraints(self, c: VarConstraints, name: str, is_element: bool) -> SimpleTypeName:
        if c.hard_exact is not None:
            if c.hard_min_chain is not None:
                if c.hard_exact != c.hard_min_chain and (
                    c.hard_min_chain == SimpleTypeName.FLOAT and c.hard_exact == SimpleTypeName.INT
                ):
                    self.diagnostics.append(
                        f"Unsatisfiable constraints for {name}{'[element]' if is_element else ''}: "
                        f"requires at least FLOAT but exactly INT"
                    )
            return c.hard_exact

        if c.hard_min_chain is not None:
            if c.soft_preference is not None:
                if c.soft_preference == c.hard_min_chain:
                    return c.soft_preference
            return c.hard_min_chain

        if c.soft_preference is not None:
            return c.soft_preference

        return SimpleTypeName.STRING


def type_check(program: AwkProgram) -> InferenceResult:
    checker = AwkTypeChecker()
    return checker.type_program(program)


if __name__ == "__main__":
    from stream.special_signatures._awk.parser import parse_awk_program

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

    result = type_check(parse_awk_program(program_text))
    print(result)


