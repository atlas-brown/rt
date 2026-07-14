import pytest

from rt.shell.parser import parse_pipelines
from rt.type_checking.annotations import (
    CommandAnnotationKind,
    EnvAnnotationKind,
)


def _parse(script: str):
    return list(parse_pipelines(script))


def _cmd_anns(script: str, cmd_idx: int = 0):
    pipeline = _parse(script)[0]
    return pipeline.commands[cmd_idx][1]


def _env(script: str):
    return _parse(script)[0].env


# ---------------------------------------------------------------------------
# Colon form — command kinds (parametrised)
# ---------------------------------------------------------------------------

_CMD_KINDS = [
    ("assume_input", CommandAnnotationKind.ASSUME_INPUT),
    ("assume_output", CommandAnnotationKind.ASSUME_OUTPUT),
    ("assert_input", CommandAnnotationKind.ASSERT_INPUT),
    ("assert_output", CommandAnnotationKind.ASSERT_OUTPUT),
    ("assert_input_contains", CommandAnnotationKind.ASSERT_INPUT_CONTAINS),
    ("assert_output_contains", CommandAnnotationKind.ASSERT_OUTPUT_CONTAINS),
]


@pytest.mark.parametrize("kw,kind", _CMD_KINDS)
def test_colon_command_kind_double_quoted(kw, kind):
    script = f'''
# @{kw} "cat" : "[0-9]+"
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert len(anns) == 1
    assert anns[0].kind == kind
    assert anns[0].command_str == "cat"
    assert anns[0].regex == "[0-9]+"


@pytest.mark.parametrize("kw,kind", _CMD_KINDS)
def test_colon_command_kind_single_quoted(kw, kind):
    script = f"""
# @{kw} 'cat' : '[0-9]+'
echo hi | cat
"""
    anns = _cmd_anns(script, 1)
    assert len(anns) == 1
    assert anns[0].kind == kind
    assert anns[0].command_str == "cat"
    assert anns[0].regex == "[0-9]+"


@pytest.mark.parametrize("kw,kind", _CMD_KINDS)
def test_colon_command_kind_unquoted(kw, kind):
    script = f'''
# @{kw} cat : [0-9]+
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert len(anns) == 1
    assert anns[0].kind == kind
    assert anns[0].command_str == "cat"
    assert anns[0].regex == "[0-9]+"


# ---------------------------------------------------------------------------
# Colon form — env kinds
# ---------------------------------------------------------------------------

def test_colon_var():
    script = '''
# @var HOME : "[a-z]+"
echo hi | cat
'''
    env = _env(script)
    assert "HOME" in env
    ann = env["HOME"][0]
    assert ann.kind == EnvAnnotationKind.VAR
    assert ann.name == "HOME"
    assert ann.regex == "[a-z]+"


def test_colon_var_unquoted():
    script = '''
# @var PATH : [^\\n]*
echo hi | cat
'''
    env = _env(script)
    assert "PATH" in env
    ann = env["PATH"][0]
    assert ann.kind == EnvAnnotationKind.VAR
    assert ann.name == "PATH"
    assert ann.regex == "[^\\n]*"


def test_colon_file():
    script = '''
# @file data.txt : "[0-9]+"
echo hi | cat
'''
    env = _env(script)
    assert "data.txt" in env
    ann = env["data.txt"][0]
    assert ann.kind == EnvAnnotationKind.FILE
    assert ann.name == "data.txt"
    assert ann.regex == "[0-9]+"


def test_colon_concretize(tmp_path):
    data_file = tmp_path / "data.txt"
    data_file.write_text("hello\nworld\n")

    script = f'''
# @concretize var : {data_file}
echo hi | cat
'''
    env = _env(script)
    assert "var" in env
    ann = env["var"][0]
    assert ann.kind == EnvAnnotationKind.CONCRETIZE
    assert ann.name == "var"
    assert "hello" in ann.regex
    assert "world" in ann.regex


# ---------------------------------------------------------------------------
# Colon form — quoting edge cases
# ---------------------------------------------------------------------------

def test_colon_mixed_quoting():
    script = '''
# @assume_input "echo hi" : '[0-9]+'
echo hi | cat
'''
    anns = _cmd_anns(script, 0)
    assert anns[0].kind == CommandAnnotationKind.ASSUME_INPUT
    assert anns[0].command_str == "echo hi"
    assert anns[0].regex == "[0-9]+"


def test_colon_command_str_preserved_as_written():
    """command_str is stored exactly as written in the annotation (quotes stripped)."""
    script = '''
# @assume_output "grep foo" : "[a-z]+"
# @assume_output 'grep bar' : '[0-9]+'
echo hi | grep foo | grep bar
'''
    anns1 = _cmd_anns(script, 1)
    anns2 = _cmd_anns(script, 2)
    assert anns1[0].command_str == "grep foo"
    assert anns2[0].command_str == "grep bar"


# ---------------------------------------------------------------------------
# Arrow form — disambiguation (parametrised)
# ---------------------------------------------------------------------------

_ARROW_CASES = [
    # (annotation_line, expected_kind, expected_cmd_str, expected_regex)
    ("@assume 'cat' -> '[0-9]+'", CommandAnnotationKind.ASSUME_OUTPUT, "cat", "[0-9]+"),
    ("@assume '[0-9]+' -> 'cat'", CommandAnnotationKind.ASSUME_INPUT, "cat", "[0-9]+"),
    ("@assert 'cat' -> '[a-z]+'", CommandAnnotationKind.ASSERT_OUTPUT, "cat", "[a-z]+"),
    ("@assert '[a-z]+' -> 'cat'", CommandAnnotationKind.ASSERT_INPUT, "cat", "[a-z]+"),
    ("@assert_contains 'cat' -> '[a-z]+'", CommandAnnotationKind.ASSERT_OUTPUT_CONTAINS, "cat", "[a-z]+"),
    ("@assert_contains '[a-z]+' -> 'cat'", CommandAnnotationKind.ASSERT_INPUT_CONTAINS, "cat", "[a-z]+"),
]


@pytest.mark.parametrize("anno,expected_kind,expected_cmd,expected_regex", _ARROW_CASES)
def test_arrow_disambiguation(anno, expected_kind, expected_cmd, expected_regex):
    script = f'''
# {anno}
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert len(anns) == 1
    assert anns[0].kind == expected_kind
    assert anns[0].command_str == expected_cmd
    assert anns[0].regex == expected_regex


# ---------------------------------------------------------------------------
# Arrow form — ambiguous (should produce no annotations)
# ---------------------------------------------------------------------------

_ARROW_AMBIGUOUS = [
    #                              sides that match (left or both)
    ("@assume 'echo hi' -> 'cat'", "both match commands"),
    ("@assume 'zzz' -> 'yyy'",     "neither matches"),
    ("@assert 'echo hi' -> 'cat'", "both match commands"),
    ("@assert 'zzz' -> 'yyy'",     "neither matches"),
    ("@assert_contains 'echo hi' -> 'cat'", "both match commands"),
    ("@assert_contains 'zzz' -> 'yyy'",     "neither matches"),
]


@pytest.mark.parametrize("anno,_reason", _ARROW_AMBIGUOUS)
def test_arrow_ambiguous_skipped(anno, _reason):
    script = f'''
# {anno}
echo hi | cat
'''
    for _, anns in _parse(script)[0].commands:
        assert len(anns) == 0


# ---------------------------------------------------------------------------
# Arrow form — quoting
# ---------------------------------------------------------------------------

_ARROW_QUOTING = [
    ("@assume 'cat' -> \"[0-9]+\"", CommandAnnotationKind.ASSUME_OUTPUT, "cat", "[0-9]+"),
    ("@assume \"[a-z]+\" -> 'cat'", CommandAnnotationKind.ASSUME_INPUT, "cat", "[a-z]+"),
    ("@assert_contains cat -> [0-9]+", CommandAnnotationKind.ASSERT_OUTPUT_CONTAINS, "cat", "[0-9]+"),
]


@pytest.mark.parametrize("anno,kind,cmd,regex", _ARROW_QUOTING)
def test_arrow_quoting(anno, kind, cmd, regex):
    script = f'''
# {anno}
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert anns[0].kind == kind
    assert anns[0].command_str == cmd
    assert anns[0].regex == regex


# ---------------------------------------------------------------------------
# Multiple annotations — same command
# ---------------------------------------------------------------------------

def test_multiple_annotations_same_command():
    script = '''
# @assume_output "cat" : "[0-9]+"
# @assert_output "cat" : "[a-z]+"
# @assert_output_contains "cat" : "[x]+"
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert len(anns) == 3
    assert anns[0].kind == CommandAnnotationKind.ASSUME_OUTPUT
    assert anns[1].kind == CommandAnnotationKind.ASSERT_OUTPUT
    assert anns[2].kind == CommandAnnotationKind.ASSERT_OUTPUT_CONTAINS


# ---------------------------------------------------------------------------
# Multiple annotations — different commands
# ---------------------------------------------------------------------------

def test_multiple_annotations_different_commands():
    script = '''
# @assume_output "sort" : "[0-9]+"
# @assert_input "grep foo" : "[a-z]+"
# @var HOME : "[^\\n]*"
echo hi | sort | grep foo
'''
    anns_sort = _cmd_anns(script, 1)
    anns_grep = _cmd_anns(script, 2)
    env = _env(script)

    assert len(anns_sort) == 1
    assert anns_sort[0].kind == CommandAnnotationKind.ASSUME_OUTPUT
    assert anns_sort[0].command_str == "sort"

    assert len(anns_grep) == 1
    assert anns_grep[0].kind == CommandAnnotationKind.ASSERT_INPUT
    assert anns_grep[0].command_str == "grep foo"

    assert env["HOME"][0].kind == EnvAnnotationKind.VAR


# ---------------------------------------------------------------------------
# Scan behaviour
# ---------------------------------------------------------------------------

def test_scan_skips_blank_lines_and_comments():
    script = '''
# @assume_output "cat" : "[a-z]+"

# this is an explanatory comment
# @assume_output "cat" : "[0-9]+"
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert len(anns) == 2
    assert anns[0].regex == "[a-z]+"
    assert anns[1].regex == "[0-9]+"


def test_scan_stops_at_non_annotation_line():
    script = '''
# @assume_output "cat" : "[a-z]+"
echo "not an annotation"
# @assume_output "cat" : "[0-9]+"
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert len(anns) == 1
    assert anns[0].regex == "[0-9]+"


def test_no_annotations():
    script = '''
echo hi | cat
'''
    pipeline = _parse(script)[0]
    for _, anns in pipeline.commands:
        assert len(anns) == 0
    assert len(pipeline.env) == 0


def test_consecutive_annotations():
    script = '''
# @assume_output "cat" : "[a-z]+"
# @assert_input "cat" : "[0-9]+"
# @var V1 : "[^\\n]*"
# @file f.txt : "[a]+"
# @assert_output "cat" : "[x]+"
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    cmd_kinds = [a.kind for a in anns]
    # Stored in top-to-bottom order
    assert cmd_kinds == [
        CommandAnnotationKind.ASSUME_OUTPUT,
        CommandAnnotationKind.ASSERT_INPUT,
        CommandAnnotationKind.ASSERT_OUTPUT,
    ]
    env = _env(script)
    assert env["V1"][0].kind == EnvAnnotationKind.VAR
    assert env["f.txt"][0].kind == EnvAnnotationKind.FILE


# ---------------------------------------------------------------------------
# Whitespace / formatting
# ---------------------------------------------------------------------------

def test_tabs_as_whitespace():
    script = """\
#\t@assume_input\tcat\t:\t[0-9]+
echo hi | cat
"""
    anns = _cmd_anns(script, 1)
    assert len(anns) == 1
    assert anns[0].kind == CommandAnnotationKind.ASSUME_INPUT
    assert anns[0].command_str == "cat"
    assert anns[0].regex == "[0-9]+"


def test_extra_spaces_around_separator():
    script = '''
# @assume_input    cat  :  [0-9]+
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert len(anns) == 1
    assert anns[0].kind == CommandAnnotationKind.ASSUME_INPUT
    assert anns[0].command_str == "cat"
    assert anns[0].regex == "[0-9]+"


def test_leading_whitespace_in_annotation_comment():
    script = '''\
   # @assume_input cat : [0-9]+
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert len(anns) == 1
    assert anns[0].kind == CommandAnnotationKind.ASSUME_INPUT


# ---------------------------------------------------------------------------
# Command matching
# ---------------------------------------------------------------------------

def test_command_with_flags_matches():
    script = '''
# @assume_output "head -n 5" : "[0-9]+"
echo hi | head -n 5 | cat
'''
    anns = _cmd_anns(script, 1)
    assert len(anns) == 1
    assert anns[0].command_str == "head -n 5"


def test_command_not_in_pipeline_skipped():
    script = '''
# @assume_output "zzz" : "[0-9]+"
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert len(anns) == 0


# ---------------------------------------------------------------------------
# Mixed colon and arrow forms
# ---------------------------------------------------------------------------

def test_mixed_colon_and_arrow():
    script = '''
# @assume_input cat : [0-9]+
# @assume cat -> [a-z]+
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    kinds = [a.kind for a in anns]
    assert kinds == [
        CommandAnnotationKind.ASSUME_INPUT,
        CommandAnnotationKind.ASSUME_OUTPUT,
    ]


# ---------------------------------------------------------------------------
# Multiple env annotations
# ---------------------------------------------------------------------------

def test_multiple_env_annotations():
    script = '''
# @var HOME : "[a-z]+"
# @var PATH : "[^\\n]*"
# @file data.txt : "[0-9]+"
echo hi | cat
'''
    env = _env(script)
    assert env["HOME"][0].kind == EnvAnnotationKind.VAR
    assert env["PATH"][0].kind == EnvAnnotationKind.VAR
    assert env["data.txt"][0].kind == EnvAnnotationKind.FILE


# ---------------------------------------------------------------------------
# Empty pipelines
# ---------------------------------------------------------------------------

def test_empty_script_produces_no_pipelines():
    script = ""
    pipelines = _parse(script)
    assert len(pipelines) == 0


# ---------------------------------------------------------------------------
# Regex with literal backslash sequences
# ---------------------------------------------------------------------------

def test_regex_with_literal_newline_and_tab():
    script = '''
# @assume_output "cat" : "[^\\n\\t]+"
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert anns[0].regex == r"[^\n\t]+"


def test_regex_with_escaped_special_chars():
    script = '''
# @assume_output "cat" : "\\(hello\\)\\+\\.\\*"
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert anns[0].regex == "\\(hello\\)\\+\\.\\*"


def test_regex_with_anchors_and_quantifiers():
    script = '''
# @assume_output "cat" : "^[a-z]{3,5}$"
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert anns[0].regex == "^[a-z]{3,5}$"


def test_regex_with_set_and_negation():
    script = '''
# @assert_input "cat" : "[^a-z0-9]"
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert anns[0].regex == "[^a-z0-9]"


def test_regex_unquoted_with_special_chars():
    script = '''
# @assume_output cat : [0-9]|[a-f]+
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert anns[0].regex == "[0-9]|[a-f]+"


# ---------------------------------------------------------------------------
# Arrow — identical sides
# ---------------------------------------------------------------------------

_ARROW_IDENTICAL = [
    "@assume 'cat' -> 'cat'",
    "@assert 'cat' -> 'cat'",
    "@assert_contains 'cat' -> 'cat'",
    "@assume 'echo hi' -> 'echo hi'",
    "@assert 'echo hi' -> 'echo hi'",
    "@assert_contains 'echo hi' -> 'echo hi'",
]


@pytest.mark.parametrize("anno", _ARROW_IDENTICAL)
def test_arrow_identical_sides_skipped(anno):
    script = f'''
# {anno}
echo hi | cat
'''
    for _, anns in _parse(script)[0].commands:
        assert len(anns) == 0


def test_arrow_identical_sides_unmatched_also_skipped():
    script = '''
# @assert "zzz" -> "zzz"
echo hi | cat
'''
    for _, anns in _parse(script)[0].commands:
        assert len(anns) == 0


# ---------------------------------------------------------------------------
# Scan skips non-annotation comments but stops at code
# ---------------------------------------------------------------------------

def test_scan_skips_descriptive_comments():
    script = '''
# @assume_output "cat" : "[0-9]+"
# the command below is important, its output must be only digits
# @assert_output "cat" : "[a-z]+"
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert len(anns) == 2
    assert anns[0].kind == CommandAnnotationKind.ASSUME_OUTPUT
    assert anns[1].kind == CommandAnnotationKind.ASSERT_OUTPUT


def test_scan_stops_at_actual_code_line():
    script = '''
# @assume_output "cat" : "[a-z]+"
echo "actual shell command"
# @assume_output "cat" : "[0-9]+"
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert len(anns) == 1
    assert anns[0].regex == "[0-9]+"


# ---------------------------------------------------------------------------
# Quoted special characters — colon/arrow inside quoted values
# ---------------------------------------------------------------------------

_QUOTED_SPECIAL_CHARS = [
    # Colon inside double-quoted regex
    ('@assume_output cat : "[a-z]:[0-9]"',
     CommandAnnotationKind.ASSUME_OUTPUT, "cat", "[a-z]:[0-9]"),
    # Colon inside single-quoted regex
    ("@assert_output cat : '[a-z]:[0-9]'",
     CommandAnnotationKind.ASSERT_OUTPUT, "cat", "[a-z]:[0-9]"),
    # Arrow inside double-quoted regex
    ('@assume cat -> "[a-z] -> [0-9]"',
     CommandAnnotationKind.ASSUME_OUTPUT, "cat", "[a-z] -> [0-9]"),
    # Arrow inside single-quoted regex
    ("@assert cat -> '[a-z] -> [0-9]'",
     CommandAnnotationKind.ASSERT_OUTPUT, "cat", "[a-z] -> [0-9]"),
    # Arrow between two single-quoted values containing arrows
    ("@assert 'x -> y' -> 'a -> b'",
     None, None, None),  # neither side matches a pipeline command → skipped
]


@pytest.mark.parametrize("anno,kind,cmd,regex", _QUOTED_SPECIAL_CHARS)
def test_quoted_special_characters_not_parsed_as_separators(anno, kind, cmd, regex):
    script = f'''
# {anno}
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    if kind is None:
        assert len(anns) == 0
    else:
        assert len(anns) == 1
        assert anns[0].kind == kind
        assert anns[0].command_str == cmd
        assert anns[0].regex == regex


# ---------------------------------------------------------------------------
# Template holes ({{...}}) in annotation regexes
# ---------------------------------------------------------------------------

_HOLE_REGEXES = [
    # {{input}} — double-quoted
    ('@assume_output cat : "{{input}}"', "{{input}}"),
    # {{$1}} — single-quoted
    ("@assume_output cat : '{{$1}}'", "{{$1}}"),
    # {{@$1}} — double-quoted
    ('@assume_output cat : "{{@$1}}"', "{{@$1}}"),
    # {{$@}} — unquoted
    ("@assume_output cat : {{$@}}", "{{$@}}"),
    # {{d$@}} — double-quoted
    ('@assume_output cat : "{{d$@}}"', "{{d$@}}"),
    # Arrow form with {{input}}
    ("@assume cat -> '{{input}}'", "{{input}}"),
]


@pytest.mark.parametrize("anno,expected_regex", _HOLE_REGEXES)
def test_template_holes_preserved_in_regex(anno, expected_regex):
    script = f'''
# {anno}
echo hi | cat
'''
    anns = _cmd_anns(script, 1)
    assert len(anns) == 1
    assert anns[0].regex == expected_regex
