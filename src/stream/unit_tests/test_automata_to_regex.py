import random
import string
import time

from stream.automata_to_regex import automaton_to_regex
from stream.regex_parser import (
    CharacterClass,
    Concatenate,
    Dot,
    Literal,
    Range,
    Repeat,
    Union,
    ast_to_regex,
)
from stream.regular_type import RegularType, readable_automata_repr
from stream.rt_cli import _strip_regular_type


def assert_equivalent(left, right) -> None:
    assert left.subsetOf(right)
    assert right.subsetOf(left)


def minimized_automaton(pattern: str):
    automaton = RegularType(pattern).nfa.clone()
    automaton.setDeterministic(False)
    automaton.removeDeadTransitions()
    automaton.determinize()
    automaton.minimize()
    return automaton


def transition_count(automaton) -> int:
    return sum(len(list(state.getTransitions())) for state in automaton.getStates())


def translate_with_elapsed(automaton, **kwargs):
    start = time.perf_counter()
    converted = automaton_to_regex(automaton, **kwargs)
    return converted, time.perf_counter() - start


def large_literal(seed: int, length: int) -> str:
    rng = random.Random(seed)
    alphabet = string.ascii_letters + string.digits + "_-"
    return "".join(rng.choice(alphabet) for _ in range(length))


def literal_ast(text: str):
    if not text:
        return Literal("")
    if len(text) == 1:
        return Literal(text)
    return Concatenate([Literal(char) for char in text])


def concat_ast(*nodes):
    return Concatenate(list(nodes))


def char_class_ast(start: str, end: str):
    return CharacterClass(False, [Range(start, end)])


def rendered(ast) -> str:
    return ast_to_regex(ast)


def random_literal_tree(rng: random.Random, text: str):
    if not text:
        return Literal("")
    if len(text) == 1:
        return Literal(text)
    split = rng.randint(1, len(text) - 1)
    return Concatenate([
        random_literal_tree(rng, text[:split]),
        random_literal_tree(rng, text[split:]),
    ])


def random_star_tree(rng: random.Random, base, leaves: int):
    if leaves <= 1:
        return Repeat(base, 0, None)

    split = rng.randint(1, leaves - 1)
    left = random_star_tree(rng, base, split)
    right = random_star_tree(rng, base, leaves - split)
    op = rng.randrange(5)
    if op < 2:
        return Union(left, right)
    if op < 4:
        return Concatenate([left, right])
    return Repeat(Concatenate([left, right]), rng.choice([0, 1]), rng.choice([None, 1, 3]))


def random_hard_tree(rng: random.Random, leaves: int, union_budget: int = 3):
    if leaves <= 1:
        return Repeat(Literal(rng.choice("abcd0123_-")), 0, rng.randint(6, 12))

    split = rng.randint(1, leaves - 1)
    left_budget = rng.randint(0, union_budget)
    right_budget = union_budget - left_budget
    left = random_hard_tree(rng, split, left_budget)
    right = random_hard_tree(rng, leaves - split, right_budget)

    if union_budget > 0 and rng.randrange(5) == 0:
        return Union(left, right)
    node = Concatenate([left, right])
    if rng.randrange(7) == 0:
        return Repeat(node, 0, 1)
    return node


def tree_regex_at_least(ast_factory, target_length: int) -> str:
    leaves = max(2, target_length // 12)
    while True:
        pattern = rendered(ast_factory(leaves))
        if len(pattern) >= target_length:
            return pattern
        leaves = int(leaves * 1.5) + 1


def large_shape_regexes() -> list[str]:
    cases: list[str] = []
    for seed in range(20):
        rng = random.Random(seed)
        literal = random_literal_tree(rng, large_literal(seed, 64 + seed * 16))
        dot_star = Repeat(Dot(), 0, None)
        cases.extend(
            [
                rendered(literal),
                rendered(concat_ast(literal, dot_star)),
                rendered(concat_ast(dot_star, literal)),
                rendered(concat_ast(dot_star, literal, dot_star)),
            ]
        )

    collapsible_language_asts = [
        Repeat(char_class_ast("0", "9"), 0, None),
        Repeat(char_class_ast("a", "z"), 0, None),
        Repeat(char_class_ast("A", "Z"), 1, None),
        Repeat(CharacterClass(True, [Literal(" ")]), 0, None),
        concat_ast(
            Repeat(char_class_ast("a", "f"), 1, None),
            Repeat(char_class_ast("a", "f"), 0, None),
        ),
    ]
    for seed in range(20):
        rng = random.Random(seed)
        parts = []
        atom = rng.choice(collapsible_language_asts)
        while len(rendered(concat_ast(*parts))) < 260:
            parts.append(atom)
        cases.append(rendered(concat_ast(*parts)))

    return cases


def generated_regex(seed: int, target_length: int = 180) -> str:
    rng = random.Random(seed)
    bases = [
        Repeat(char_class_ast("0", "9"), 0, None),
        Repeat(char_class_ast("a", "z"), 0, None),
        Repeat(char_class_ast("A", "Z"), 0, None),
        Repeat(CharacterClass(True, [Literal(" ")]), 0, None),
        Repeat(Union(char_class_ast("a", "f"), char_class_ast("a", "f")), 0, None),
        Repeat(Union(char_class_ast("0", "9"), char_class_ast("0", "9")), 0, None),
        Repeat(Union(char_class_ast("a", "z"), char_class_ast("a", "z")), 0, None),
    ]
    base = rng.choice(bases)
    return tree_regex_at_least(
        lambda leaves: random_star_tree(rng, base, leaves),
        target_length,
    )


def generated_hard_regex(seed: int, target_length: int = 180) -> str:
    rng = random.Random(seed)
    return tree_regex_at_least(
        lambda leaves: random_hard_tree(rng, leaves, union_budget=3),
        target_length,
    )


def generated_readable_regex(seed: int, target_length: int = 180) -> str:
    rng = random.Random(seed + 10_000)
    literal = random_literal_tree(rng, large_literal(seed + 10_000, max(180, target_length)))
    shape = (seed // 4) % 2
    if shape == 0:
        return rendered(literal)
    return rendered(concat_ast(literal, Repeat(Dot(), 0, None)))


def assert_round_trip_is_equivalent_and_readable(original: str) -> str:
    original_automaton = minimized_automaton(original)
    length_budget = max(256, len(original) * 30)

    converted, elapsed = translate_with_elapsed(
        original_automaton,
        max_states=48,
        max_transitions=420,
        max_regex_length=length_budget,
        max_edge_length=length_budget,
    )

    assert converted is not None, (
        original,
        len(original),
        len(original_automaton.getStates()),
        transition_count(original_automaton),
    )
    assert elapsed < 1.0, (original, elapsed)
    assert len(converted) <= length_budget, (original, converted)
    assert_equivalent(original_automaton, minimized_automaton(converted))
    return converted


def test_large_structured_regexes_round_trip_and_stay_readable():
    cases = large_shape_regexes()
    assert len(cases) >= 100
    assert min(len(case) for case in cases) >= 48
    assert max(len(case) for case in cases) >= 360

    for original in cases:
        assert_round_trip_is_equivalent_and_readable(original)


def test_large_generated_regexes_round_trip_when_automata_are_moderate():
    successes = 0
    fallbacks = 0
    for seed in range(120):
        target_length = 320 + (seed * 17) % 320
        if seed % 4 == 0:
            original = generated_readable_regex(seed, target_length=target_length)
        elif seed % 4 == 1:
            original = generated_regex(seed, target_length=target_length)
        else:
            original = generated_hard_regex(seed, target_length=target_length)
        assert len(original) >= 320
        original_automaton = minimized_automaton(original)
        if len(original_automaton.getStates()) > 48 or transition_count(original_automaton) > 420:
            fallbacks += 1
            converted, elapsed = translate_with_elapsed(
                original_automaton,
                max_states=12,
                max_transitions=120,
                max_regex_length=4096,
                max_edge_length=4096,
            )
            assert elapsed < 0.5
            if converted is None:
                continue

        length_budget = max(256, len(original) * 30)
        converted, elapsed = translate_with_elapsed(
            original_automaton,
            max_states=48,
            max_transitions=420,
            max_regex_length=length_budget,
            max_edge_length=length_budget,
        )
        assert elapsed < 1.0, (original, elapsed)
        if converted is None:
            fallbacks += 1
            continue
        assert len(converted) <= length_budget, (original, converted)
        assert_equivalent(original_automaton, minimized_automaton(converted))
        successes += 1

    assert successes >= 30
    assert fallbacks >= 40


def test_automaton_repr_is_raw_by_default_for_benchmark_path():
    rendered = repr(RegularType(automaton=minimized_automaton(".*foo.*")))
    assert rendered.startswith("RegularType(Automaton)\n")


def test_common_automaton_only_regular_types_are_human_readable_when_enabled():
    for pattern in [".*", ".+", "[0-9]+", "[^ ]*", "foo"]:
        with readable_automata_repr(True):
            rendered = repr(RegularType(automaton=minimized_automaton(pattern)))
        assert rendered == f"RegularType({pattern})"


def test_contains_literal_uses_short_readable_candidate_for_long_literals():
    literal = large_literal(9001, 128)
    for pattern in [literal, literal + ".*", ".*" + literal, ".*" + literal + ".*"]:
        converted, _ = translate_with_elapsed(minimized_automaton(pattern))
        assert converted == pattern


def test_large_automata_are_rejected_before_state_elimination_explodes():
    large = minimized_automaton("a{0,80}")

    converted, elapsed = translate_with_elapsed(large, max_states=4)

    assert converted is None
    assert elapsed < 0.5

    rendered = repr(RegularType(automaton=large))
    assert rendered.startswith("RegularType(Automaton)\n")


def test_rt_cli_uses_readable_regular_type_and_preserves_automaton_fallback():
    with readable_automata_repr(True):
        readable = repr(RegularType(automaton=minimized_automaton(".*foo.*")))
    assert _strip_regular_type(readable) == ".*foo.*"

    with readable_automata_repr(True):
        fallback = repr(RegularType(automaton=minimized_automaton("a{0,80}")))
    assert fallback.startswith("RegularType(Automaton)\n")
    assert _strip_regular_type(fallback).startswith("RegularType(Automaton)\n")
