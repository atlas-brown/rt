from pathlib import Path

import pytest
from pash_annotations.datatypes.BasicDatatypes import Flag, Operand
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from rtr import main as rtr_main
from stream.command_type_parser import (
    parse_command_type_annotation,
    parse_transform_expression,
)
from stream.regular_type import RegularType
from stream.signature_loader import SignatureLoader


def _resolve_signature(signature_dir, invocation):
    SignatureLoader.reset_instance()
    loader = SignatureLoader.get_instance(signature_dir.as_posix())
    return loader.find_signature(invocation)


def test_cli_registers_simple_invocation_annotation(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "rtr",
            "--signature-dir",
            tmp_path.as_posix(),
            "--type",
            ".* -> [0-9]+",
            "whoami",
        ],
    )

    rtr_main.cli_main()

    output = capsys.readouterr().out
    assert "Registered type annotation:" in output
    assert "whoami" in output
    assert ".* -> [0-9]+" in output
    assert list(tmp_path.glob("whoami__annotation_*.yaml"))


def test_cli_registers_polymorphic_invocation_annotation(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "rtr",
            "--signature-dir",
            tmp_path.as_posix(),
            "--type",
            "forall a . [a-z]+ -> a",
            "tee",
        ],
    )

    rtr_main.cli_main()

    output = capsys.readouterr().out
    assert "Registered type annotation:" in output
    assert "tee" in output
    assert "[a-z]+ -> [a-z]+" in output
    assert list(tmp_path.glob("tee__annotation_*.yaml"))


def test_cli_registers_option_value_specific_annotation(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "rtr",
            "--signature-dir",
            tmp_path.as_posix(),
            "--type",
            ".* -> [0-9]+",
            "tail",
            "-n",
            "3",
        ],
    )

    rtr_main.cli_main()

    registration_output = capsys.readouterr().out
    assert "tail -n 3" in registration_output
    assert ".* -> [0-9]+" in registration_output

    rtr_main.main("tail", ["-n", "3"], RegularType(".*"), signature_dir=tmp_path)
    exact_output = capsys.readouterr().out
    assert ".* -> [0-9]+" in exact_output

    rtr_main.main("tail", ["-n", "4"], RegularType(".*"), signature_dir=tmp_path)
    other_output = capsys.readouterr().out
    assert ".* -> .*" in other_output


def test_specific_invocation_annotation_precedes_generic_signature(tmp_path, apply_signature):
    (tmp_path / "customcmd.yaml").write_text(
        "\n".join(
            [
                'command_name: "customcmd"',
                'default_input_type: ".*"',
                'default_output_type: ".*"',
                "args: []",
                "flags: []",
                "rules: []",
                "isInteresting: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    specific_invocation = CommandInvocationInitial(
        "customcmd",
        [Flag("-n")],
        [Operand("status")],
    )
    rtr_main.register_invocation_type(
        specific_invocation,
        tmp_path,
        ".* -> [0-9]+",
    )

    specific_signature = _resolve_signature(tmp_path, specific_invocation)
    generic_signature = _resolve_signature(
        tmp_path,
        CommandInvocationInitial("customcmd", [], [Operand("other")]),
    )

    specific_result = apply_signature(
        specific_signature,
        RegularType(""),
        specific_invocation,
    )
    generic_result = apply_signature(
        generic_signature,
        RegularType("abc"),
        CommandInvocationInitial("customcmd", [], [Operand("other")]),
    )

    assert specific_signature.match
    assert specific_result.pattern == "[0-9]+"
    assert generic_signature.match == {}
    assert generic_result.pattern == ".*"


def test_invocation_annotation_overrides_special_signature_only_for_exact_invocation(
    tmp_path,
    apply_signature,
):
    (tmp_path / "grep.yaml").write_text(
        Path("src/stream/signatures/grep.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    exact_invocation = CommandInvocationInitial("grep", [], [Operand("foo")])
    other_invocation = CommandInvocationInitial("grep", [], [Operand("bar")])
    rtr_main.register_invocation_type(
        exact_invocation,
        tmp_path,
        ".* -> [0-9]+",
    )

    SignatureLoader.reset_instance()
    loader = SignatureLoader.get_instance(tmp_path.as_posix())
    exact_signature = loader.find_signature(exact_invocation)
    other_signature = loader.find_signature(other_invocation)

    exact_result = apply_signature(
        exact_signature,
        RegularType("foo"),
        exact_invocation,
    )
    other_result = apply_signature(
        other_signature,
        RegularType("bar"),
        other_invocation,
    )

    assert exact_signature.match
    assert exact_signature.__class__.__name__ == "CommandSignature"
    assert exact_result.pattern == "[0-9]+"
    assert other_signature.match == {}
    assert other_signature.__class__.__name__ == "GrepSignature"
    assert other_result.pattern != "[0-9]+"


def test_command_type_parser_supports_simple_and_forall_annotations():
    simple = parse_command_type_annotation("[0-9]+ -> [0-9]+")
    polymorphic = parse_command_type_annotation("forall a . a -> a")
    nested = parse_command_type_annotation(
        'forall a . [ab]+ -> reverse(translate-match(a, "a", "b", global=true))'
    )

    assert simple.input_type == "[0-9]+"
    assert simple.output_type == "[0-9]+"
    assert simple.polymorphic is False
    assert polymorphic.input_type == ".*"
    assert polymorphic.output_type == "{{actual_input_type}}"
    assert polymorphic.polymorphic is True
    assert nested.input_type == "[ab]+"
    assert (
        nested.output_type
        == 'reverse(translate-match({{actual_input_type}}, "a", "b", global=true))'
    )
    assert nested.polymorphic is True


def test_transform_expression_preserves_regex_leading_space():
    output_type = parse_transform_expression(" *[0-9]+").apply(RegularType(".*"))

    assert RegularType(" 0").is_subtype(output_type)[0]
    assert not RegularType("[*]0").is_subtype(output_type)[0]


@pytest.mark.parametrize(
    ("annotation", "expected_input", "expected_output"),
    [
        (
            'forall a . [ab]+ -> translate-chars(delete-chars(a, "a"), "b", "c", squeeze=true)',
            "[ab]+",
            'translate-chars(delete-chars({{actual_input_type}}, "a"), "b", "c", squeeze=true)',
        ),
        (
            'forall a . [a-z0-9]+ -> union(line-extract(a, "[0-9]+"), reverse(a))',
            "[a-z0-9]+",
            'union(line-extract({{actual_input_type}}, "[0-9]+"), reverse({{actual_input_type}}))',
        ),
        (
            'forall a . .+ -> compose(reverse(a), translate-match(a, "a,b", "x,y", global=true))',
            ".+",
            'compose(reverse({{actual_input_type}}), translate-match({{actual_input_type}}, "a,b", "x,y", global=true))',
        ),
        (
            "forall a . .+ -> default-if-empty(head-lines(a, 2), tail-lines(a, 1))",
            ".+",
            "default-if-empty(head-lines({{actual_input_type}}, 2), tail-lines({{actual_input_type}}, 1))",
        ),
        (
            "forall a . .+ -> concat(intersect(a, [a-z]+), optional(union(a, reverse(a))))",
            ".+",
            "concat(intersect({{actual_input_type}}, [a-z]+), optional(union({{actual_input_type}}, reverse({{actual_input_type}}))))",
        ),
        (
            'forall a . .+ -> field-select(line-extract(a, "[^,]+"), ",", "1-2", invert=true)',
            ".+",
            'field-select(line-extract({{actual_input_type}}, "[^,]+"), ",", "1-2", invert=true)',
        ),
    ],
)
def test_command_type_parser_normalizes_complex_nested_operators(
    annotation,
    expected_input,
    expected_output,
):
    parsed = parse_command_type_annotation(annotation)

    assert parsed.input_type == expected_input
    assert parsed.output_type == expected_output
    assert parsed.polymorphic is True


@pytest.mark.parametrize(
    ("annotation", "expected_output"),
    [
        (
            "forall a . .+ -> a|[0-9]+",
            "{{actual_input_type}}|[0-9]+",
        ),
        (
            "forall a . .+ -> a&[a-z]+",
            "{{actual_input_type}}&[a-z]+",
        ),
        (
            "forall a . .+ -> ~a",
            "~{{actual_input_type}}",
        ),
        (
            "forall a . .+ -> a?",
            "{{actual_input_type}}?",
        ),
        (
            "forall a . .+ -> a*",
            "{{actual_input_type}}*",
        ),
        (
            "forall a . .+ -> a[a-z]+",
            "{{actual_input_type}}[a-z]+",
        ),
        (
            "forall a . .+ -> (a|[0-9]+)[A-Z]?",
            "({{actual_input_type}}|[0-9]+)[A-Z]?",
        ),
        (
            "forall a . .+ -> ((a|[0-9]+)&~([A-Z]+))[a]?",
            "(({{actual_input_type}}|[0-9]+)&~([A-Z]+))[a]?",
        ),
        (
            "forall a . .+ -> a[a]",
            "{{actual_input_type}}[a]",
        ),
    ],
)
def test_command_type_parser_normalizes_direct_regular_type_operators(
    annotation,
    expected_output,
):
    parsed = parse_command_type_annotation(annotation)

    assert parsed.input_type == ".+"
    assert parsed.output_type == expected_output
    assert parsed.polymorphic is True


@pytest.mark.parametrize(
    ("annotation", "input_type"),
    [
        (
            'forall a . [ab]+ -> translate-chars(delete-chars(a, "a"), "b", "c", squeeze=true)',
            RegularType("[ab]+"),
        ),
        (
            'forall a . [a-z0-9]+ -> union(line-extract(a, "[0-9]+"), reverse(a))',
            RegularType("[a-z0-9]+"),
        ),
        (
            'forall a . .+ -> compose(reverse(a), translate-match(a, "a,b", "x,y", global=true))',
            RegularType("a,b"),
        ),
        (
            "forall a . .+ -> default-if-empty(head-lines(a, 2), tail-lines(a, 1))",
            RegularType("a\\nb\\n"),
        ),
        (
            "forall a . .+ -> concat(intersect(a, [a-z]+), optional(union(a, reverse(a))))",
            RegularType("[a-z]+"),
        ),
        (
            'forall a . .+ -> field-select(line-extract(a, "[^,]+"), ",", "1-2", invert=true)',
            RegularType("a,b,c"),
        ),
    ],
)
def test_complex_nested_operator_command_types_apply(annotation, input_type):
    command_type = parse_command_type_annotation(annotation).to_command_type()

    result = command_type.apply_to_input(input_type)

    assert isinstance(result, RegularType)


@pytest.mark.parametrize(
    "annotation",
    [
        "forall a . .+ -> a|[0-9]+",
        "forall a . .+ -> a&[a-z]+",
        "forall a . .+ -> ~a",
        "forall a . .+ -> a?",
        "forall a . .+ -> a*",
        "forall a . .+ -> a+",
        "forall a . .+ -> a[a-z]+",
        "forall a . .+ -> (a|[0-9]+)[A-Z]?",
        "forall a . .+ -> ((a|[0-9]+)&~([A-Z]+))[a]?",
    ],
)
def test_direct_regular_type_operator_command_types_apply(annotation):
    command_type = parse_command_type_annotation(annotation).to_command_type()

    result = command_type.apply_to_input(RegularType("[a-z]+"))

    assert isinstance(result, RegularType)


def test_cli_registers_polymorphic_regular_operator(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "rtr",
            "--signature-dir",
            tmp_path.as_posix(),
            "--type",
            "forall a . [a-z]+ -> reverse(a)",
            "customcmd",
        ],
    )

    rtr_main.cli_main()

    output = capsys.readouterr().out
    assert "Registered type annotation:" in output
    assert "[a-z]+ -> ([a-z]+)^R" in output


def test_cli_registers_direct_regular_type_operator_annotation(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "rtr",
            "--signature-dir",
            tmp_path.as_posix(),
            "--type",
            "forall a . [a-z]+ -> (a|[0-9]+)[A-Z]?",
            "customcmd",
        ],
    )

    rtr_main.cli_main()

    output = capsys.readouterr().out
    yaml_text = next(tmp_path.glob("customcmd__annotation_*.yaml")).read_text(
        encoding="utf-8"
    )

    assert "Registered type annotation:" in output
    assert "[a-z]+ -> (([a-z]+)|(([0-9])+))(([A-Z])?)" in output
    assert "output_type: ({{actual_input_type}}|[0-9]+)[A-Z]?" in yaml_text


def test_cli_regular_operator_annotation_allows_automaton_output(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "rtr",
            "--signature-dir",
            tmp_path.as_posix(),
            "--type",
            'forall a . [ab]+ -> translate-match(a, "a", "b", global=true)',
            "customcmd",
        ],
    )

    rtr_main.cli_main()

    output = capsys.readouterr().out
    assert "Registered type annotation:" in output
    assert "Type:" in output


def test_cli_registers_nested_regular_operator_annotation(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "rtr",
            "--signature-dir",
            tmp_path.as_posix(),
            "--type",
            'forall a . [ab]+ -> reverse(translate-match(a, "a", "b", global=true))',
            "customcmd",
        ],
    )

    rtr_main.cli_main()

    output = capsys.readouterr().out
    yaml_text = next(tmp_path.glob("customcmd__annotation_*.yaml")).read_text(
        encoding="utf-8"
    )

    assert "Registered type annotation:" in output
    assert "Type:" in output
    assert (
        'output_type: reverse(translate-match({{actual_input_type}}, "a", "b", global=true))'
        in yaml_text
    )
