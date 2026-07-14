from unittest.mock import MagicMock, patch

from pash_annotations.datatypes.BasicDatatypes import Flag, Operand, Option
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import (
    RuleResolver,
    _parse_transform_expression,
    _substitute_shell_vars,
    build_env,
    resolve_annotation_pattern,
)
from rt.regular_types.stream_transform import Constant, Input
from rt.regular_types.stream_type import StreamType


class TestParseTransformExpression:
    def test_empty_returns_input(self):
        result = _parse_transform_expression("", {})
        assert isinstance(result, Input)

    def test_whitespace_only_is_regex(self):
        from rt.regular_types.stream_transform import Regex as RegexTransform
        result = _parse_transform_expression("   ", {})
        assert isinstance(result, RegexTransform)

    def test_known_hole_returns_env_value(self):
        env = {"foo": Input()}
        result = _parse_transform_expression("{{foo}}", env)
        assert result is env["foo"]

    def test_hole_with_whitespace(self):
        env = {"foo": Input()}
        result = _parse_transform_expression("{{  foo  }}", env)
        assert result is env["foo"]

    def test_input_hole(self):
        env = {"input": Input()}
        result = _parse_transform_expression("{{input}}", env)
        assert isinstance(result, Input)

    def test_unknown_hole_raises_valueerror(self):
        try:
            _parse_transform_expression("{{unknown}}", {})
            assert False, "expected ValueError"
        except ValueError:
            pass

    def test_actual_input_type_no_longer_recognized(self):
        try:
            _parse_transform_expression("{{actual_input_type}}", {})
            assert False, "expected ValueError for removed artifact"
        except ValueError:
            pass

    def test_regex_fallback(self):
        env = {"input": Input()}
        from rt.regular_types.stream_transform import Regex as RegexTransform
        result = _parse_transform_expression("[0-9]+", env)
        assert isinstance(result, RegexTransform)

    def test_at_prefix_falls_through_to_env(self):
        env = {"@$1": Input()}
        result = _parse_transform_expression("{{@$1}}", env)
        assert result is env["@$1"]

    def test_atat_prefix_falls_through_to_env(self):
        env = {"@@$1": Input()}
        result = _parse_transform_expression("{{@@$1}}", env)
        assert result is env["@@$1"]

    def test_at_prefix_strips_and_looks_up_env(self):
        env = {"input": Input()}
        result = _parse_transform_expression("{{@input}}", env)
        assert result is env["input"]

    def test_atat_prefix_strips_and_looks_up_env(self):
        env = {"input": Input()}
        result = _parse_transform_expression("{{@@input}}", env)
        assert result is env["input"]

    def test_dollar_n_hole_via_env(self):
        env = {"$1": Input()}
        result = _parse_transform_expression("{{$1}}", env)
        assert result is env["$1"]


class TestMatchWhen:
    def test_opts_key_is_used(self):
        resolver = RuleResolver(
            input_type=".*",
            output_type="{{input}}",
            when=[{"opts": ["-n"], "output": ".*"}],
        )
        input_pat, output_pat = resolver._match_when({"-n"})
        assert output_pat == ".*"

    def test_opts_not_matched_when_flags_differ(self):
        resolver = RuleResolver(
            input_type=".*",
            output_type="{{input}}",
            when=[{"opts": ["-n"], "output": ".*"}],
        )
        input_pat, output_pat = resolver._match_when({"-q"})
        assert output_pat == "{{input}}"

    def test_flags_fallback_still_works(self):
        resolver = RuleResolver(
            input_type=".*",
            output_type="{{input}}",
            when=[{"flags": ["-n"], "output": ".*"}],
        )
        input_pat, output_pat = resolver._match_when({"-n"})
        assert output_pat == ".*"

    def test_opts_takes_priority_over_flags(self):
        resolver = RuleResolver(
            input_type=".*",
            output_type="{{input}}",
            when=[{"opts": ["-n"], "flags": ["-q"], "output": "matched"}],
        )
        input_pat, output_pat = resolver._match_when({"-n", "-q"})
        assert output_pat == "matched"

    def test_first_match_wins(self):
        resolver = RuleResolver(
            input_type=".*",
            output_type="{{input}}",
            when=[
                {"opts": ["-n"], "output": "first"},
                {"opts": ["-n", "-l"], "output": "second"},
            ],
        )
        input_pat, output_pat = resolver._match_when({"-n", "-l"})
        assert output_pat == "first"

    def test_subset_check(self):
        resolver = RuleResolver(
            input_type=".*",
            output_type="{{input}}",
            when=[{"opts": ["-n", "-l"], "output": "matched"}],
        )
        input_pat, output_pat = resolver._match_when({"-n", "-l", "-q"})
        assert output_pat == "matched"

    def test_no_match_returns_defaults(self):
        resolver = RuleResolver(
            input_type="empty_pat",
            output_type="default_out",
            when=[],
        )
        input_pat, output_pat = resolver._match_when(set())
        assert input_pat == "empty_pat"
        assert output_pat == "default_out"

    def test_when_can_override_input_too(self):
        resolver = RuleResolver(
            input_type=".*",
            output_type="{{input}}",
            when=[{"opts": ["-n"], "input": "[0-9]+", "output": ".*"}],
        )
        input_pat, output_pat = resolver._match_when({"-n"})
        assert input_pat == "[0-9]+"


class TestBuildEnv:
    def test_input_key_always_present(self):
        inv = CommandInvocationInitial("cmd", [], [])
        with patch(
            "rt.regular_types.stream_type.StreamType.from_pattern",
            return_value=StreamType(automaton=MagicMock()),
        ):
            env = build_env(inv)
            assert "input" in env
            assert isinstance(env["input"], Input)

    def test_actual_input_type_removed(self):
        inv = CommandInvocationInitial("cmd", [], [])
        with patch(
            "rt.regular_types.stream_type.StreamType.from_pattern",
            return_value=StreamType(automaton=MagicMock()),
        ):
            env = build_env(inv)
            assert "actual_input_type" not in env

    def test_dollar_n_for_operands(self):
        inv = CommandInvocationInitial("cmd", [], [Operand("a"), Operand("b")])
        with patch(
            "rt.regular_types.stream_type.StreamType.from_pattern",
            return_value=StreamType(automaton=MagicMock()),
        ):
            env = build_env(inv)
            assert "$1" in env
            assert "$2" in env
            assert isinstance(env["$1"], Constant)
            assert isinstance(env["$2"], Constant)

    def test_at_dollar_n_and_atat_dollar_n_for_operands(self):
        inv = CommandInvocationInitial("cmd", [], [Operand("x")])
        with patch(
            "rt.regular_types.stream_type.StreamType.from_pattern",
            return_value=StreamType(automaton=MagicMock()),
        ):
            env = build_env(inv)
            assert "@$1" in env
            assert "@@$1" in env
            assert isinstance(env["@$1"], Constant)
            assert isinstance(env["@@$1"], Constant)

    def test_dollar_at_with_operands(self):
        inv = CommandInvocationInitial("cmd", [], [Operand("a"), Operand("b")])
        with patch(
            "rt.regular_types.stream_type.StreamType.from_pattern",
            return_value=StreamType(automaton=MagicMock()),
        ):
            env = build_env(inv)
            assert "$@" in env

    def test_fallback_when_no_operands(self):
        inv = CommandInvocationInitial("cmd", [], [])
        with patch(
            "rt.regular_types.stream_type.StreamType.from_pattern",
            return_value=StreamType(automaton=MagicMock()),
        ):
            env = build_env(inv)
            assert "$1" in env
            assert "@$1" in env
            assert "@@$1" in env
            assert "$@" in env

    def test_option_args_populated(self):
        inv = CommandInvocationInitial(
            "paste", [Option("-d", ",")], [Operand("f1"), Operand("f2")]
        )
        with patch(
            "rt.regular_types.stream_type.StreamType.from_pattern",
            return_value=StreamType(automaton=MagicMock()),
        ):
            env = build_env(inv)
            assert "d$1" in env
            assert "d$@" in env
            assert isinstance(env["d$1"], Constant)
            assert isinstance(env["d$@"], Constant)

    def test_multiple_option_args_indexed(self):
        inv = CommandInvocationInitial(
            "cmd", [Option("-d", "x"), Option("-d", "y")], []
        )
        with patch(
            "rt.regular_types.stream_type.StreamType.from_pattern",
            return_value=StreamType(automaton=MagicMock()),
        ):
            env = build_env(inv)
            assert "d$1" in env
            assert "d$2" in env

    def test_multiple_options_separate_letters(self):
        inv = CommandInvocationInitial(
            "cmd",
            [Option("-d", "x"), Option("-k", "1,2")],
            [],
        )
        with patch(
            "rt.regular_types.stream_type.StreamType.from_pattern",
            return_value=StreamType(automaton=MagicMock()),
        ):
            env = build_env(inv)
            assert "d$1" in env
            assert "d$@" in env
            assert "k$1" in env
            assert "k$@" in env

    def test_flags_without_args_do_not_create_option_entries(self):
        inv = CommandInvocationInitial("cmd", [Flag("-n"), Flag("-l")], [])
        with patch(
            "rt.regular_types.stream_type.StreamType.from_pattern",
            return_value=StreamType(automaton=MagicMock()),
        ):
            env = build_env(inv)
            assert "n$1" not in env
            assert "l$1" not in env


class TestRuleResolverResolve:
    def test_heuristic_rules_accepted_as_kwarg(self):
        resolver = RuleResolver()
        inv = CommandInvocationInitial("cmd", [Flag("-n")], [Operand("hello")])
        with patch(
            "rt.regular_types.stream_type.StreamType.from_pattern",
            return_value=StreamType(automaton=MagicMock()),
        ):
            env = build_env(inv)
        result = resolver.resolve(
            inv, [], env, heuristic_rules=["no_meaningless_command"]
        )
        assert isinstance(result, CommandType)


class TestResolveAnnotationPattern:
    def test_plain_regex(self):
        result = resolve_annotation_pattern("[0-9]+", {})
        assert isinstance(result, StreamType)

    def test_input_hole(self):
        env = {"input": Input()}
        inp = StreamType(automaton=MagicMock())
        result = resolve_annotation_pattern("{{input}}", env, input=inp)
        # {{input}} resolves to Input() which returns the input StreamType
        assert result is inp

    def test_dollar_n_hole(self):
        literal_type = StreamType(automaton=MagicMock())
        env = {"$1": Constant(literal_type)}
        result = resolve_annotation_pattern("{{$1}}", env)
        assert result is literal_type

    def test_hole_with_no_input_falls_back_to_dot_star(self):
        env = {"input": Input()}
        result = resolve_annotation_pattern("{{input}}", env)
        # No input provided, so defaults to ".*"
        assert isinstance(result, StreamType)

    def test_mixed_pattern_input_hole_is_resolved(self):
        env = {"input": Input()}
        inp = StreamType.from_pattern("[a-z]+")
        result = resolve_annotation_pattern("prefix{{input}}suffix", env, input=inp)
        assert isinstance(result, StreamType)

    def test_mixed_pattern_dollar_n_hole_is_resolved(self):
        literal_type = StreamType.from_pattern("hello")
        env = {"input": Input(), "$1": Constant(literal_type)}
        result = resolve_annotation_pattern("[{{$1}}]+", env)
        assert isinstance(result, StreamType)


class TestSubstituteShellVars:
    @staticmethod
    def _var_st(pattern: str) -> Constant:
        st = StreamType(
            automaton=StreamType.from_pattern(pattern).automaton,
            regex=pattern,
        )
        return Constant(st)

    def test_dollar_var_resolved(self):
        env = {"var:HOME": self._var_st("[a-z]+")}
        result = _substitute_shell_vars("$HOME", env)
        assert result == "[a-z]+"

    def test_braced_var_resolved(self):
        env = {"var:HOME": self._var_st("[a-z]+")}
        result = _substitute_shell_vars("${HOME}", env)
        assert result == "[a-z]+"

    def test_unknown_var_returns_wildcard(self):
        result = _substitute_shell_vars("$UNKNOWN", {})
        assert result == "[^\n]*"

    def test_mixed_literal_and_var(self):
        env = {"var:NAME": self._var_st("[A-Z]+")}
        result = _substitute_shell_vars("Hello $NAME", env)
        assert result == "Hello [A-Z]+"

    def test_multiple_vars(self):
        env = {
            "var:A": self._var_st("[0-9]"),
            "var:B": self._var_st("[a-z]"),
        }
        result = _substitute_shell_vars("$A-$B", env)
        assert result == "[0-9]-[a-z]"

    def test_no_vars_returns_unchanged(self):
        result = _substitute_shell_vars("literal", {})
        assert result == "literal"

    def test_entry_not_constant_returns_wildcard(self):
        env = {"var:X": Input()}
        result = _substitute_shell_vars("$X", env)
        assert result == "[^\n]*"

    def test_entry_with_none_regex_returns_wildcard(self):
        st = StreamType(automaton=StreamType.from_pattern(".*").automaton, regex=None)
        env = {"var:X": Constant(st)}
        result = _substitute_shell_vars("$X", env)
        assert result == "[^\n]*"
