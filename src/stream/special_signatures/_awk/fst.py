from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

from stream.tool_error import ToolError
from stream.transducer_utils import FST, create_fst

from stream.special_signatures._awk.parser import (
    AwkAction,
    AwkExpression,
    AwkPattern,
    AwkProgram,
    AwkRule,
    BeginPattern,
    BinaryOperation,
    EndPattern,
    FieldReference,
    IfStatement,
    NumberLiteral,
    PrintStatement,
    PrintfStatement,
    StringLiteral,
    Variable,
    parse_awk_program,
)


def awk_program_to_fst(program_text: str) -> FST:
    """Compile a restricted AWK program into an FST.

    Supported subset:
    - BEGIN/END blocks with only string-literal prints/printfs.
    - NR-only conditions: NR % m == r; NR >/< >=/<= k; NR ==/!= k.
    - Actions print at most one $0 per record (print $0; printf "%s", $0),
      plus any number of string literals.
    - If statements whose condition is in the above subset and whose branches
      only contain the supported print/printf forms.

    Semantics mapping:
    - Prefix literals (before $0) are emitted via not-consumed transitions before
      reading the record characters.
    - $0 maps every non-newline input char to itself at most once.
    - Suffix literals (after $0) are emitted when consuming the newline.
    - BEGIN literals are prepended to the first record's prefix.
    - END literals are appended to the unbounded bucket's suffix (best-effort).
    """

    ast = parse_awk_program(program_text)
    compiler = _AwkToFstCompiler(ast)
    return compiler.compile()


@dataclass(frozen=True)
class _StateClass:
    exact_nr: Optional[int]
    residue_mod_m: int


@dataclass
class _PerStateSchedule:
    prefix: str
    emit_self: bool
    suffix: str


class _AwkToFstCompiler:
    def __init__(self, program: AwkProgram):
        self.program: AwkProgram = program
        self.max_threshold: int = 0
        self.modulus: int = 1
        self._begin_literal: str = ""
        self._end_literal: str = ""
        self._analyze_requirements()

    def compile(self) -> FST:
        states: List[_StateClass] = self._enumerate_states()

        schedules: Dict[_StateClass, _PerStateSchedule] = {}
        for idx, sc in enumerate(states):
            prefix, emit_self, suffix = self._compute_schedule_for_state(sc)
            if idx == 0 and self._begin_literal:
                prefix = self._begin_literal + prefix
            if sc.exact_nr is None and self._end_literal:
                suffix = suffix + self._end_literal
            schedules[sc] = _PerStateSchedule(prefix=prefix, emit_self=emit_self, suffix=suffix)

        specs: List[Tuple[int, str, str, int] | Tuple[int, str, str, int, bool]] = []

        def sid(idx: int) -> Tuple[int, int]:
            base = 2 * idx + 1
            return base, base + 1

        for idx, sc in enumerate(states):
            start_id, read_id = sid(idx)
            schedule = schedules[sc]
            # Always add not-consumed pass-through, prefix may be empty
            specs.append((start_id, "$all", schedule.prefix, read_id, True))

            if schedule.emit_self:
                specs.append((read_id, "$other", "$self", read_id))
            else:
                specs.append((read_id, "$other", "", read_id))

            next_idx = self._next_state_index(states, idx)
            next_start_id, _ = sid(next_idx)
            specs.append((read_id, "\n", schedule.suffix, next_start_id))

        final_states = set()
        for idx in range(len(states)):
            start_id, read_id = sid(idx)
            final_states.add(start_id)
            final_states.add(read_id)
        return create_fst(specs, start_state=sid(0)[0], final_states=final_states)

    def _analyze_requirements(self) -> None:
        for rule in self.program.rules:
            if isinstance(rule.pattern, BeginPattern):
                self._begin_literal += self._flatten_literal_only_action(rule.action)
                continue
            if isinstance(rule.pattern, EndPattern):
                self._end_literal += self._flatten_literal_only_action(rule.action)
                continue
            if rule.pattern is not None:
                self._collect_expr_reqs_from_pattern(rule.pattern)
            self._collect_reqs_from_action(rule.action)
        if self.modulus <= 0:
            raise ToolError("Invalid modulus computed")

    def _collect_expr_reqs_from_pattern(self, pattern: AwkPattern) -> None:
        from stream.special_signatures._awk.parser import ExpressionPattern as _ExpressionPattern
        if isinstance(pattern, _ExpressionPattern):
            self._collect_reqs_from_expression(pattern.expression)
        elif not isinstance(pattern, (BeginPattern, EndPattern)):
            raise ToolError("Unsupported AWK pattern: only NR expressions/BEGIN/END allowed")

    def _collect_reqs_from_expression(self, expr: AwkExpression) -> None:
        if isinstance(expr, BinaryOperation):
            op = expr.operator
            if op == "%":
                m = self._const_int(expr.right)
                if not isinstance(expr.left, Variable) or expr.left.name != "NR":
                    raise ToolError("Left side of % must be NR")
                if m <= 0:
                    raise ToolError("Modulo by non-positive integer is unsupported")
                self.modulus = _lcm(self.modulus, m)
                return
            if op in ("==", "!=", "<", "<=", ">", ">="):
                self._collect_reqs_from_expression(expr.left)
                self._collect_reqs_from_expression(expr.right)
                nr_left = isinstance(expr.left, Variable) and expr.left.name == "NR"
                nr_right = isinstance(expr.right, Variable) and expr.right.name == "NR"
                if nr_left ^ nr_right:
                    k = self._const_int(expr.right if nr_left else expr.left)
                    self.max_threshold = max(self.max_threshold, k)
                return
        if isinstance(expr, Variable):
            if expr.name != "NR":
                raise ToolError("Only NR variable supported in conditions")
            return
        if isinstance(expr, NumberLiteral):
            return
        raise ToolError("Unsupported expression in condition; only NR and integers with %, ==, !=, <, <=, >, >=")

    def _collect_reqs_from_action(self, action: AwkAction) -> None:
        for stmt in action.statements:
            if isinstance(stmt, IfStatement):
                self._collect_reqs_from_expression(stmt.condition)
                self._ensure_print_only(stmt.then_action)
                if stmt.else_action:
                    self._ensure_print_only(stmt.else_action)
            elif isinstance(stmt, (PrintStatement, PrintfStatement)):
                _ = self._flatten_stmt_to_tokens(stmt, probe_only=True)
            else:
                raise ToolError("Only print/printf/if statements are supported in actions")

    def _ensure_print_only(self, action: AwkAction) -> None:
        for stmt in action.statements:
            if isinstance(stmt, IfStatement):
                self._ensure_print_only(stmt.then_action)
                if stmt.else_action:
                    self._ensure_print_only(stmt.else_action)
            elif isinstance(stmt, (PrintStatement, PrintfStatement)):
                _ = self._flatten_stmt_to_tokens(stmt, probe_only=True)
            else:
                raise ToolError("Only print/printf allowed in if branches")

    def _enumerate_states(self) -> List[_StateClass]:
        states: List[_StateClass] = []
        m = max(self.modulus, 1)
        if self.max_threshold <= 0:
            initial_residue = 1 % m
            for step in range(m):
                residue = (initial_residue + step) % m
                states.append(_StateClass(exact_nr=None, residue_mod_m=residue))
            return states
        for i in range(1, self.max_threshold + 1):
            states.append(_StateClass(exact_nr=i, residue_mod_m=i % m))
        start_residue = (self.max_threshold + 1) % m
        for step in range(m):
            residue = (start_residue + step) % m
            states.append(_StateClass(exact_nr=None, residue_mod_m=residue))
        return states

    def _next_state_index(self, states: List[_StateClass], idx: int) -> int:
        sc = states[idx]
        m = max(self.modulus, 1)
        if sc.exact_nr is not None:
            next_nr = sc.exact_nr + 1
            if next_nr <= self.max_threshold:
                return next((j for j, s in enumerate(states) if s.exact_nr == next_nr), idx)
            residue = next_nr % m
            return next((j for j, s in enumerate(states) if s.exact_nr is None and s.residue_mod_m == residue), idx)
        residue = (sc.residue_mod_m + 1) % m
        return next((j for j, s in enumerate(states) if s.exact_nr is None and s.residue_mod_m == residue), idx)

    def _compute_schedule_for_state(self, sc: _StateClass) -> Tuple[str, bool, str]:
        events: List[Union[str, Tuple[str, ...]]] = []
        nr_value = self._representative_nr(sc)
        for rule in self.program.rules:
            if isinstance(rule.pattern, (BeginPattern, EndPattern)):
                continue
            if rule.pattern is None:
                matched = True
            else:
                from stream.special_signatures._awk.parser import ExpressionPattern as _ExpressionPattern
                if isinstance(rule.pattern, _ExpressionPattern):
                    matched = self._eval_condition(rule.pattern.expression, nr_value)
                else:
                    raise ToolError("Unsupported pattern (only NR expression patterns supported)")
            if not matched:
                continue
            self._append_action_events(rule.action, nr_value, events)
        prefix_parts: List[str] = []
        suffix_parts: List[str] = []
        seen_self = False
        for ev in events:
            if isinstance(ev, tuple) and ev and ev[0] == "$0":
                if seen_self:
                    raise ToolError("$0 is printed more than once in the matched rules for a record")
                seen_self = True
            else:
                if not seen_self:
                    prefix_parts.append(ev)
                else:
                    suffix_parts.append(ev)
        return ("".join(prefix_parts), seen_self, "".join(suffix_parts))

    def _append_action_events(self, action: AwkAction, nr_value: int, out: List[Union[str, Tuple[str, ...]]]) -> None:
        for stmt in action.statements:
            if isinstance(stmt, IfStatement):
                branch = stmt.then_action if self._eval_condition(stmt.condition, nr_value) else stmt.else_action
                if branch:
                    self._append_action_events(branch, nr_value, out)
                continue
            if isinstance(stmt, (PrintStatement, PrintfStatement)):
                tokens = self._flatten_stmt_to_tokens(stmt, probe_only=False)
                out.extend(tokens)
                continue
            raise ToolError("Unsupported statement in action; only if/print/printf supported")

    def _flatten_literal_only_action(self, action: AwkAction) -> str:
        collected: List[str] = []
        self._ensure_print_only(action)
        for stmt in action.statements:
            tokens = self._flatten_stmt_to_tokens(stmt, probe_only=False)
            if any(isinstance(t, tuple) and t and t[0] == "$0" for t in tokens):
                raise ToolError("BEGIN/END must not print $0 in this subset")
            for t in tokens:
                if isinstance(t, str):
                    collected.append(t)
        return "".join(collected)

    def _flatten_stmt_to_tokens(
        self, stmt: Union[PrintStatement, PrintfStatement], *, probe_only: bool
    ) -> List[Union[str, Tuple[str, ...]]]:
        tokens: List[Union[str, Tuple[str, ...]]] = []
        if isinstance(stmt, PrintStatement):
            exprs = list(stmt.expressions)
            if len(exprs) == 0:
                tokens.append(("$0",))
                tokens.append("\n")
                return tokens
            if len(exprs) != 1:
                raise ToolError("Only single-expression print is supported")
            e = exprs[0]
            if isinstance(e, FieldReference) and _is_dollar_zero(e):
                tokens.append(("$0",))
                tokens.append("\n")
                return tokens
            if isinstance(e, StringLiteral):
                tokens.append(e.value + "\n")
                return tokens
            raise ToolError("Unsupported print expression; only $0 or string literal")
        fmt = stmt.format_string
        if not isinstance(fmt, StringLiteral):
            raise ToolError("Only string literal formats are supported in printf")
        fmt_text = fmt.value
        args = list(stmt.arguments)
        if len(args) == 0:
            tokens.append(fmt_text)
            return tokens
        if len(args) == 1 and fmt_text == "%s" and isinstance(args[0], FieldReference) and _is_dollar_zero(args[0]):
            tokens.append(("$0",))
            return tokens
        raise ToolError("Unsupported printf form; only printf \"literal\" or printf \"%s\", $0")

    def _eval_condition(self, expr: AwkExpression, nr_value: int) -> bool:
        val = self._eval_expr(expr, nr_value)
        if isinstance(val, bool):
            return val
        if isinstance(val, int):
            raise ToolError("Conditions must be boolean comparisons over NR")
        raise ToolError("Unsupported condition expression")

    def _eval_expr(self, expr: AwkExpression, nr_value: int) -> Union[int, bool]:
        if isinstance(expr, NumberLiteral):
            if not isinstance(expr.value, int) and not (isinstance(expr.value, float) and expr.value.is_integer()):
                raise ToolError("Only integer numeric literals are supported")
            return int(expr.value)
        if isinstance(expr, Variable):
            if expr.name != "NR":
                raise ToolError("Only NR variable supported in expressions")
            return nr_value
        if isinstance(expr, BinaryOperation):
            op = expr.operator
            if op in ("+", "-", "*", "/", "%"):
                left = self._eval_expr(expr.left, nr_value)
                right = self._eval_expr(expr.right, nr_value)
                if not isinstance(left, int) or not isinstance(right, int):
                    raise ToolError("Arithmetic requires integer operands")
                if op == "+":
                    return left + right
                if op == "-":
                    return left - right
                if op == "*":
                    return left * right
                if op == "/":
                    if right == 0:
                        raise ToolError("Division by zero")
                    return left // right
                if op == "%":
                    if right <= 0:
                        raise ToolError("Modulo by non-positive integer is unsupported")
                    return left % right
            if op in ("==", "!=", "<", "<=", ">", ">="):
                left_v = self._eval_expr(expr.left, nr_value)
                right_v = self._eval_expr(expr.right, nr_value)
                if not isinstance(left_v, int) or not isinstance(right_v, int):
                    raise ToolError("Comparisons require integer operands")
                if op == "==":
                    return left_v == right_v
                if op == "!=":
                    return left_v != right_v
                if op == "<":
                    return left_v < right_v
                if op == "<=":
                    return left_v <= right_v
                if op == ">":
                    return left_v > right_v
                if op == ">=":
                    return left_v >= right_v
        raise ToolError("Unsupported expression form")

    def _const_int(self, expr: AwkExpression) -> int:
        if isinstance(expr, NumberLiteral):
            if isinstance(expr.value, int):
                return expr.value
            if isinstance(expr.value, float) and expr.value.is_integer():
                return int(expr.value)
        raise ToolError("Expected integer literal")

    def _representative_nr(self, sc: _StateClass) -> int:
        if sc.exact_nr is not None:
            return sc.exact_nr
        base = self.max_threshold + 1
        m = max(self.modulus, 1)
        rem = base % m
        if rem == sc.residue_mod_m:
            return base
        delta = (sc.residue_mod_m - rem) % m
        return base + delta


def _lcm(a: int, b: int) -> int:
    from math import gcd

    if a == 0 or b == 0:
        return max(1, a, b)
    return abs(a * b) // gcd(a, b)


def _is_dollar_zero(field: FieldReference) -> bool:
    return isinstance(field.index, NumberLiteral) and int(field.index.value) == 0


if __name__ == "__main__":
    awk_program = "NR % 5 == 1 { printf \"[\" }  { printf \"%s\", $0 }  {if (NR % 5 == 0) { printf \"]\\n\" } else { printf \", \" }}"
    print(parse_awk_program(awk_program))
    fst = awk_program_to_fst(awk_program)
    print(fst)
    print(fst.transform_all("1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n"))

    awk_program = "NR > 1 { printf \", \" } { printf \"%s\", $0 }"
    print(parse_awk_program(awk_program))
    fst = awk_program_to_fst(awk_program)
    print(fst)
    print(fst.transform_all("1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n"))