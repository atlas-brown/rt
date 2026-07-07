import functools
import itertools
from dataclasses import dataclass

from collections.abc import Iterable

from rt.constants import ALPHABET_SIZE
from rt.java_api import (
    Automaton,
    AutomatonState,
    AutomatonTransition,
)
from rt.regex import parse_regex

_DEFAULT_MAX_STATES = 24
_DEFAULT_MAX_TRANSITIONS = 180
_DEFAULT_MAX_REGEX_LENGTH = 4096
_DEFAULT_MAX_EDGE_LENGTH = 2048
_RAW_STATE_BUDGET_FACTOR = 8
_RAW_TRANSITION_BUDGET_FACTOR = 16

_META_CHARS = "^$.*+?{}[]()|&~\\"


def _regex_escape_literal(ch: str) -> str:
    return "\\" + ch if ch in _META_CHARS else ch


class RegexConversionBudgetExceeded(Exception):
    pass


@dataclass(frozen=True)
class RegexConversionConfig:
    max_states: int = _DEFAULT_MAX_STATES
    max_transitions: int = _DEFAULT_MAX_TRANSITIONS
    max_regex_length: int = _DEFAULT_MAX_REGEX_LENGTH
    max_edge_length: int = _DEFAULT_MAX_EDGE_LENGTH
    alphabet_max: int = ALPHABET_SIZE - 1
    line_based: bool = True


@dataclass(frozen=True)
class _Regex:
    text: str
    precedence: int

    @property
    def length(self) -> int:
        return len(self.text)


_EPSILON = _Regex("", 4)


@functools.lru_cache()
def get_singleton(automaton: Automaton) -> str | None:
    s = automaton.getShortestExample(True)
    if s is None:
        return None
    diff = automaton.minus(Automaton.makeString(s))
    if diff.isEmpty():
        return str(s)
    return None


def automaton_summary(automaton: Automaton) -> str:
    states = list(automaton.getStates())
    return f"<automaton: {len(states)} states, {_transition_count(states)} transitions>"


def automaton_to_regex(
    automaton: Automaton,
    *,
    max_states: int = _DEFAULT_MAX_STATES,
    max_transitions: int = _DEFAULT_MAX_TRANSITIONS,
    max_regex_length: int = _DEFAULT_MAX_REGEX_LENGTH,
    max_edge_length: int = _DEFAULT_MAX_EDGE_LENGTH,
    line_based: bool = True,
    alphabet_max: int = ALPHABET_SIZE - 1,
) -> str | None:
    """Best-effort conversion from a Brics automaton to a readable regex."""
    config = RegexConversionConfig(
        max_states=max_states,
        max_transitions=max_transitions,
        max_regex_length=max_regex_length,
        max_edge_length=max_edge_length,
        alphabet_max=alphabet_max,
        line_based=line_based,
    )
    try:
        converter = _AutomatonToRegex(config)
        return converter.convert(automaton)
    except RegexConversionBudgetExceeded:
        return None


class _AutomatonToRegex:
    def __init__(self, config: RegexConversionConfig) -> None:
        self.config = config
        self.universe = set(range(config.alphabet_max - 1))
        if config.line_based:
            self.universe.discard(ord("\n"))
        self._alphabet_automaton: Automaton | None = None

    def convert(self, automaton: Automaton) -> str:
        raw_states = list(automaton.getStates())
        raw_transition_count = _transition_count(raw_states)
        structural_fast = self._try_fast_regex(
            automaton, raw_states, include_singleton=False
        )
        if structural_fast is not None:
            return structural_fast
        if (
            len(raw_states) > self.config.max_states * _RAW_STATE_BUDGET_FACTOR
            or raw_transition_count
            > self.config.max_transitions * _RAW_TRANSITION_BUDGET_FACTOR
        ):
            raise RegexConversionBudgetExceeded()

        automaton = self._normalize(automaton)
        states = list(automaton.getStates())
        transition_count = _transition_count(states)

        candidates = self._candidate_regexes(automaton, states, transition_count)
        if (
            len(states) <= self.config.max_states
            and transition_count <= self.config.max_transitions
        ):
            candidates.append(self._state_elimination(automaton, states).text or "()")

        if not candidates:
            raise RegexConversionBudgetExceeded()

        regex = min(candidates, key=lambda candidate: (len(candidate), candidate))
        self._check_length(regex, final=True)
        return regex

    def _normalize(self, automaton: Automaton) -> Automaton:
        nfa = automaton.clone()
        nfa.setDeterministic(False)
        nfa.removeDeadTransitions()
        nfa.determinize()
        nfa.minimize()
        return nfa

    def _candidate_regexes(
        self,
        automaton: Automaton,
        states: list[AutomatonState],
        transition_count: int,
    ) -> list[str]:
        candidates: list[str] = []
        seen: set[str] = set()

        fast = self._try_fast_regex(automaton, states)
        if fast is not None:
            candidates.append(fast)
            seen.add(fast)

        checked = 0
        check_limit = self._candidate_check_limit(len(states), transition_count)
        for candidate in self._literal_shape_candidates(
            automaton, states, transition_count
        ):
            if candidate in seen:
                continue
            seen.add(candidate)
            if checked >= check_limit:
                break
            checked += 1
            if self._is_equivalent_regex(automaton, candidate):
                candidates.append(candidate)

        return candidates

    def _candidate_check_limit(self, state_count: int, transition_count: int) -> int:
        state_budget = max(1, self.config.max_states)
        transition_budget = max(1, self.config.max_transitions)
        over_budget_factor = max(
            state_count / state_budget,
            transition_count / transition_budget,
        )
        if over_budget_factor <= 1:
            return 256
        if over_budget_factor <= 2:
            return 64
        if over_budget_factor <= 4:
            return 24
        return 4

    def _try_fast_regex(
        self,
        automaton: Automaton,
        states: list[AutomatonState],
        *,
        include_singleton: bool = True,
    ) -> str | None:
        if automaton.isEmpty():
            return "~.*"
        if automaton.isEmptyString():
            return "()"

        literal_chain = self._try_literal_chain(automaton)
        if literal_chain is not None:
            return literal_chain

        if include_singleton:
            singleton = get_singleton(automaton)
            if singleton is not None:
                return "".join(_escape_literal(c) for c in singleton) or "()"

        initial = automaton.getInitialState()
        if len(states) == 1 and initial.isAccept():
            ranges = self._ranges_for_transitions(initial.getTransitions(), initial)
            if ranges is not None:
                label = self._label_for_ranges(ranges)
                if label is not None:
                    return label + "*"

        if len(states) == 2 and not initial.isAccept():
            accepts = [state for state in states if state.isAccept()]
            if len(accepts) == 1:
                accept = accepts[0]
                initial_ranges = self._ranges_for_transitions(
                    initial.getTransitions(), accept
                )
                if initial_ranges is None:
                    return None
                accept_self_ranges = self._ranges_for_transitions(
                    accept.getTransitions(), accept
                )
                label = self._label_for_ranges(initial_ranges)
                if label is None:
                    return None
                if accept_self_ranges is None:
                    return label
                if _merge_ranges(initial_ranges) == _merge_ranges(accept_self_ranges):
                    return label + "+"

        return None

    def _try_literal_chain(self, automaton: Automaton) -> str | None:
        current = automaton.getInitialState()
        seen: set[AutomatonState] = set()
        literal: list[str] = []

        while True:
            if current in seen:
                return None
            seen.add(current)
            transitions = list(current.getTransitions())

            if current.isAccept():
                if not transitions:
                    return "".join(literal) or "()"
                self_loop_ranges = self._ranges_for_transitions(transitions, current)
                if (
                    self_loop_ranges is not None
                    and _ranges_to_set(self_loop_ranges) == self.universe
                ):
                    return "".join(literal) + ".*"
                return None

            if len(transitions) != 1:
                return None
            transition = transitions[0]
            start = _char_code(transition.getMin())
            end = _char_code(transition.getMax())
            if start != end:
                return None
            try:
                literal.append(_escape_literal(chr(start)))
            except RegexConversionBudgetExceeded:
                return None
            current = transition.getDest()

    def _literal_shape_candidates(
        self,
        automaton: Automaton,
        states: list[AutomatonState],
        transition_count: int,
    ) -> Iterable[str]:
        examples = self._accepted_examples(
            automaton,
            limit=4,
            max_len=min(2048, max(32, self.config.max_regex_length // 4)),
        )
        has_accept_any_loop = any(
            self._has_full_self_loop(state) for state in states if state.isAccept()
        )
        dense_literal_matcher = transition_count > max(1, len(states) * 2)
        seen_literals: set[str] = set()
        for example in examples:
            if example == "":
                continue
            literals = [example]
            if len(example) <= 24:
                for start, end in itertools.combinations(range(len(example) + 1), 2):
                    literal = example[start:end]
                    if literal:
                        literals.append(literal)
            for literal in sorted(set(literals), key=lambda item: (-len(item), item)):
                if literal in seen_literals:
                    continue
                seen_literals.add(literal)
                try:
                    escaped = "".join(_escape_literal(char) for char in literal)
                except RegexConversionBudgetExceeded:
                    continue
                yield from self._literal_shape_variants(
                    escaped,
                    prefer_contains=has_accept_any_loop and dense_literal_matcher,
                    prefer_prefix=has_accept_any_loop and not dense_literal_matcher,
                    prefer_suffix=not has_accept_any_loop and dense_literal_matcher,
                )

    def _literal_shape_variants(
        self,
        escaped: str,
        *,
        prefer_contains: bool,
        prefer_prefix: bool,
        prefer_suffix: bool,
    ) -> Iterable[str]:
        exact = escaped
        prefix = escaped + ".*"
        suffix = ".*" + escaped
        contains = ".*" + escaped + ".*"
        if prefer_contains:
            yield contains
            yield prefix
            yield suffix
            yield exact
        elif prefer_prefix:
            yield prefix
            yield contains
            yield exact
            yield suffix
        elif prefer_suffix:
            yield suffix
            yield contains
            yield exact
            yield prefix
        else:
            yield exact
            yield prefix
            yield suffix
            yield contains

    def _has_full_self_loop(self, state: AutomatonState) -> bool:
        ranges = self._ranges_for_transitions(state.getTransitions(), state)
        return ranges is not None and _ranges_to_set(ranges) == self.universe

    def _accepted_examples(
        self, automaton: Automaton, limit: int, max_len: int
    ) -> list[str]:
        examples: list[str] = []
        remaining = automaton.clone()
        for _ in range(limit):
            example = remaining.getShortestExample(True)
            if example is None:
                break
            example = str(example)
            if len(example) > max_len:
                break
            examples.append(example)
            remaining = remaining.minus(Automaton.makeString(example))
            if remaining.isEmpty():
                break
        return examples

    def _is_equivalent_regex(self, automaton: Automaton, regex: str) -> bool:
        if len(regex) > self.config.max_regex_length:
            return False
        try:
            candidate = parse_regex(regex).to_automaton({})
            candidate = candidate.intersection(self._get_alphabet_automaton())
            candidate = self._normalize(candidate)
            return automaton.subsetOf(candidate) and candidate.subsetOf(automaton)
        except Exception:
            return False

    def _get_alphabet_automaton(self) -> Automaton:
        if self._alphabet_automaton is None:
            ranges = _set_to_ranges(sorted(self.universe))
            char_automaton = Automaton.makeEmpty()
            for start, end in ranges:
                char_automaton = char_automaton.union(Automaton.makeCharRange(chr(start), chr(end)))
            self._alphabet_automaton = char_automaton.repeat(0)
        return self._alphabet_automaton

    def _ranges_for_transitions(
        self,
        transitions: Iterable[AutomatonTransition],
        expected_dest: AutomatonState,
    ) -> list[tuple[int, int]] | None:
        ranges: list[tuple[int, int]] = []
        for transition in transitions:
            if transition.getDest() != expected_dest:
                return None
            ranges.append(
                (_char_code(transition.getMin()), _char_code(transition.getMax()))
            )
        return _merge_ranges(ranges) if ranges else None

    def _state_elimination(
        self, automaton: Automaton, states: list[AutomatonState]
    ) -> _Regex:
        q_start = AutomatonState()
        q_end = AutomatonState()
        initial = automaton.getInitialState()
        accepts = [state for state in states if state.isAccept()]
        if not accepts:
            return _Regex("~.*", 4)

        edges: dict[tuple[AutomatonState, AutomatonState], _Regex] = {}
        for state in states:
            transitions_by_dest: dict[AutomatonState, list[tuple[int, int]]] = {}
            for transition in state.getTransitions():
                dest = transition.getDest()
                transitions_by_dest.setdefault(dest, []).append(
                    (_char_code(transition.getMin()), _char_code(transition.getMax()))
                )
            for dest, ranges in transitions_by_dest.items():
                label = self._label_for_ranges(_merge_ranges(ranges))
                if label is None:
                    raise RegexConversionBudgetExceeded()
                self._put_edge(edges, state, dest, _Regex(label, 4))

        self._put_edge(edges, q_start, initial, _EPSILON)
        for accept in accepts:
            self._put_edge(edges, accept, q_end, _EPSILON)

        remaining: set[AutomatonState] = set(states)
        while remaining:
            elim = self._choose_elimination_state(remaining, edges)
            remaining.remove(elim)
            loop = edges.get((elim, elim))
            loop_star = self._star(loop) if loop is not None else None

            incoming = [
                (src, expr)
                for (src, dst), expr in list(edges.items())
                if dst == elim and src != elim
            ]
            outgoing = [
                (dst, expr)
                for (src, dst), expr in list(edges.items())
                if src == elim and dst != elim
            ]

            for src, in_expr in incoming:
                for dst, out_expr in outgoing:
                    pieces = [in_expr]
                    if loop_star is not None:
                        pieces.append(loop_star)
                    pieces.append(out_expr)
                    self._put_edge(edges, src, dst, self._concat(pieces))

            for key in [key for key in edges if key[0] == elim or key[1] == elim]:
                del edges[key]

        final = edges.get((q_start, q_end))
        if final is None:
            return _Regex("~.*", 4)
        return final

    def _choose_elimination_state(
        self,
        states: set[AutomatonState],
        edges: dict[tuple[AutomatonState, AutomatonState], _Regex],
    ) -> AutomatonState:
        def cost(state: AutomatonState) -> tuple[int, int]:
            incoming = 0
            outgoing = 0
            text_size = 0
            for (src, dst), expr in edges.items():
                if dst == state and src != state:
                    incoming += 1
                    text_size += expr.length
                if src == state and dst != state:
                    outgoing += 1
                    text_size += expr.length
                if src == state and dst == state:
                    text_size += expr.length * 2
            return incoming * outgoing, text_size

        return min(states, key=cost)

    def _put_edge(
        self,
        edges: dict[tuple[AutomatonState, AutomatonState], _Regex],
        src: AutomatonState,
        dst: AutomatonState,
        expr: _Regex,
    ) -> None:
        key = (src, dst)
        if key in edges:
            edges[key] = self._union(edges[key], expr)
        else:
            self._check_length(expr.text)
            edges[key] = expr

    def _label_for_ranges(self, ranges: list[tuple[int, int]]) -> str | None:
        ranges = _merge_ranges(_clip_ranges(ranges, 0, self.config.alphabet_max))
        if not ranges:
            return None

        chars = _ranges_to_set(ranges)
        if chars == self.universe:
            return "." if self.config.line_based else "(.|\\n)"

        if len(chars) == 1:
            return _escape_literal(chr(next(iter(chars))))

        excluded = sorted(self.universe - chars)
        if 0 < len(excluded) <= max(12, len(chars) // 2):
            negated = self._character_class(_set_to_ranges(excluded), negate=True)
            if negated is not None:
                return negated

        return self._character_class(ranges, negate=False)

    def _character_class(
        self, ranges: list[tuple[int, int]], negate: bool
    ) -> str | None:
        parts: list[str] = []
        for start, end in ranges:
            if start == end:
                escaped = _escape_char_class(chr(start))
                if escaped is None:
                    return None
                parts.append(escaped)
            else:
                start_text = _escape_char_class(chr(start))
                end_text = _escape_char_class(chr(end))
                if start_text is None or end_text is None:
                    return None
                parts.append(f"{start_text}-{end_text}")
        if not parts:
            return None
        text = "[" + ("^" if negate else "") + "".join(parts) + "]"
        self._check_length(text)
        return text

    def _union(self, left: _Regex, right: _Regex) -> _Regex:
        if left.text == right.text:
            return left
        items = sorted({self._union_branch_text(left), self._union_branch_text(right)})
        text = "|".join(items)
        self._check_length(text)
        return _Regex(text, 1)

    def _union_branch_text(self, expr: _Regex) -> str:
        if not expr.text:
            return "()"
        return self._parenthesize(expr, 1)

    def _concat(self, parts: list[_Regex]) -> _Regex:
        non_empty = [part for part in parts if part.text]
        if not non_empty:
            return _EPSILON
        text = "".join(self._parenthesize(part, 2) for part in non_empty)
        self._check_length(text)
        return _Regex(text, 2)

    def _star(self, expr: _Regex) -> _Regex:
        if not expr.text:
            return _EPSILON
        text = self._parenthesize(expr, 3) + "*"
        self._check_length(text)
        return _Regex(text, 3)

    def _parenthesize(self, expr: _Regex, parent_precedence: int) -> str:
        if not expr.text:
            return ""
        if expr.precedence < parent_precedence:
            return f"({expr.text})"
        return expr.text

    def _check_length(self, text: str, *, final: bool = False) -> None:
        limit = self.config.max_regex_length if final else self.config.max_edge_length
        if len(text) > limit:
            raise RegexConversionBudgetExceeded()


def _transition_count(states: Iterable[AutomatonState]) -> int:
    return sum(len(list(state.getTransitions())) for state in states)


def _char_code(value) -> int:
    if isinstance(value, str):
        return ord(value)
    return int(value)


def _merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []
    ordered = sorted((min(start, end), max(start, end)) for start, end in ranges)
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end + 1:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _clip_ranges(
    ranges: list[tuple[int, int]], min_value: int, max_value: int
) -> list[tuple[int, int]]:
    clipped = []
    for start, end in ranges:
        start = max(start, min_value)
        end = min(end, max_value)
        if start <= end:
            clipped.append((start, end))
    return clipped


def _ranges_to_set(ranges: list[tuple[int, int]]) -> set[int]:
    chars: set[int] = set()
    for start, end in ranges:
        chars.update(range(start, end + 1))
    return chars


def _set_to_ranges(values: list[int]) -> list[tuple[int, int]]:
    if not values:
        return []
    ranges: list[tuple[int, int]] = []
    start = prev = values[0]
    for value in values[1:]:
        if value == prev + 1:
            prev = value
            continue
        ranges.append((start, prev))
        start = prev = value
    ranges.append((start, prev))
    return ranges


def _escape_literal(char: str) -> str:
    escapes = {
        "\n": "\\n",
        "\t": "\\t",
        "\r": "\\r",
        "\v": "\\v",
        "\f": "\\f",
        "\b": "\\b",
    }
    if char in escapes:
        return escapes[char]
    if not _is_readable_char(char):
        raise RegexConversionBudgetExceeded()
    return _regex_escape_literal(char)


def _escape_char_class(char: str) -> str | None:
    escapes = {
        "\n": "\\n",
        "\t": "\\t",
        "\r": "\\r",
        "\v": "\\v",
        "\f": "\\f",
        "\b": "\\b",
    }
    if char in escapes:
        return escapes[char]
    if not _is_readable_char(char):
        return None
    if char in "\\[]^-":
        return "\\" + char
    return char


def _is_readable_char(char: str) -> bool:
    codepoint = ord(char)
    return 32 <= codepoint <= 126
