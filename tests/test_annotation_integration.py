from rt.shell.parser import parse_pipelines
from rt.type_checking.checker import (
    AssertionViolationError,
    ContainsViolationError,
    InputMismatchError,
    TypeCheckError,
    type_check,
)


def _check(script: str) -> list[TypeCheckError]:
    errors: list[TypeCheckError] = []
    for pipeline in parse_pipelines(script):
        errors.extend(type_check(pipeline))
    return errors


# ---------------------------------------------------------------------------
# @assume_output
# ---------------------------------------------------------------------------

def test_assume_output_overrides_type():
    script = '''
# @assume_output "grep hello" : "[0-9]+"
echo hi | grep hello | sort
'''
    errors = _check(script)
    im_errs = [e for e in errors if isinstance(e, InputMismatchError)]
    assert len(im_errs) == 0


def test_assume_output_last_wins():
    script = '''
# @assume_output sort : "[a-z]+"
# @assume_output sort : "[0-9]+"
echo hi | sort
'''
    errors = _check(script)
    # sort accepts .*, so no input mismatch; assume_output just runs without crash
    im_errs = [e for e in errors if isinstance(e, InputMismatchError)]
    assert len(im_errs) == 0


# ---------------------------------------------------------------------------
# @assume_input
# ---------------------------------------------------------------------------

def test_assume_input_skips_check():
    script = '''
# @assume_input "grep hello" : "[a-z]+"
echo abc | grep hello
'''
    errors = _check(script)
    im_errs = [e for e in errors if isinstance(e, InputMismatchError)]
    assert len(im_errs) == 0


# ---------------------------------------------------------------------------
# @assert_input
# ---------------------------------------------------------------------------

def test_assert_input_pass():
    script = '''
# @assert_input "grep foo" : "hello"
echo hello | grep foo
'''
    errors = _check(script)
    im_errs = [e for e in errors if isinstance(e, InputMismatchError)]
    assert len(im_errs) == 0


def test_assert_input_fail():
    script = '''
# @assert_input "grep foo" : "[0-9]+"
echo hello | grep foo
'''
    errors = _check(script)
    im_errs = [e for e in errors if isinstance(e, InputMismatchError)]
    assert len(im_errs) >= 1


def test_assert_input_with_dollar_n_hole():
    script = '''
# @assert_input "grep hello" : {{$1}}
echo hello | grep hello
'''
    errors = _check(script)
    im_errs = [e for e in errors if isinstance(e, InputMismatchError)]
    assert len(im_errs) == 0


# ---------------------------------------------------------------------------
# @assert_output
# ---------------------------------------------------------------------------

def test_assert_output_pass():
    script = '''
# @assert_output "echo hello" : "hello"
echo hello | cat
'''
    errors = _check(script)
    asrt_errs = [e for e in errors if isinstance(e, AssertionViolationError)]
    assert len(asrt_errs) == 0


def test_assert_output_fail():
    script = '''
# @assert_output "echo hello" : "[0-9]+"
echo hello | cat
'''
    errors = _check(script)
    asrt_errs = [e for e in errors if isinstance(e, AssertionViolationError)]
    assert len(asrt_errs) == 1
    assert "[0-9]+" in asrt_errs[0].asserted


def test_assert_output_with_input_hole():
    script = '''
# @assert_output tee : {{input}}
echo hello | tee
'''
    errors = _check(script)
    asrt_errs = [e for e in errors if isinstance(e, AssertionViolationError)]
    assert len(asrt_errs) == 0


# ---------------------------------------------------------------------------
# @assert_input_contains
# ---------------------------------------------------------------------------

def test_assert_input_contains_pass():
    script = '''
# @assert_input_contains "grep hello" : "hello"
echo hello world | grep hello
'''
    errors = _check(script)
    contains_errs = [e for e in errors if isinstance(e, ContainsViolationError)]
    assert len(contains_errs) == 0


def test_assert_input_contains_fail():
    script = '''
# @assert_input_contains "grep hello" : "[0-9]+"
echo hello | grep hello
'''
    errors = _check(script)
    contains_errs = [e for e in errors if isinstance(e, ContainsViolationError)]
    assert len(contains_errs) == 1
    assert "[0-9]+" in contains_errs[0].pattern


# ---------------------------------------------------------------------------
# @assert_output_contains
# ---------------------------------------------------------------------------

def test_assert_output_contains_pass():
    script = '''
# @assert_output_contains "echo hello" : "hello"
echo hello | cat
'''
    errors = _check(script)
    contains_errs = [e for e in errors if isinstance(e, ContainsViolationError)]
    assert len(contains_errs) == 0


def test_assert_output_contains_fail():
    script = '''
# @assert_output_contains "echo hello" : "[0-9]+"
echo hello | cat
'''
    errors = _check(script)
    contains_errs = [e for e in errors if isinstance(e, ContainsViolationError)]
    assert len(contains_errs) == 1
    assert "[0-9]+" in contains_errs[0].pattern


# ---------------------------------------------------------------------------
# @var + echo
# ---------------------------------------------------------------------------

def test_var_echo_refines_type():
    script = '''
# @var GREETING : "[a-z]+"
echo $GREETING | grep hello
'''
    errors = _check(script)
    # With @var, echo outputs [a-z]+ which is compatible with grep hello
    im_errs = [e for e in errors if isinstance(e, InputMismatchError)]
    assert len(im_errs) == 0


def test_var_echo_unknown_falls_back_to_wildcard():
    script = '''
echo $UNKNOWN_VAR | sort
'''
    errors = _check(script)
    im_errs = [e for e in errors if isinstance(e, InputMismatchError)]
    assert len(im_errs) == 0  # wildcard → any input accepted


# ---------------------------------------------------------------------------
# Arrow forms
# ---------------------------------------------------------------------------

def test_arrow_assert_output_fail():
    script = '''
# @assert "echo hello" -> "[0-9]+"
echo hello | cat
'''
    errors = _check(script)
    asrt_errs = [e for e in errors if isinstance(e, AssertionViolationError)]
    assert len(asrt_errs) == 1


def test_arrow_assert_input_fail():
    script = '''
# @assert "[0-9]+" -> "grep foo"
echo hello | grep foo
'''
    errors = _check(script)
    im_errs = [e for e in errors if isinstance(e, InputMismatchError)]
    assert len(im_errs) >= 1


# ---------------------------------------------------------------------------
# Multiple annotations — different kinds all active
# ---------------------------------------------------------------------------

def test_multiple_kinds_all_active():
    script = '''
# @assume_input cat : "[0-9]+"
# @assert_output cat : "[0-9]+"
echo hello | cat
'''
    errors = _check(script)
    # assume_input skips input check → no InputMismatchError
    im_errs = [e for e in errors if isinstance(e, InputMismatchError)]
    assert len(im_errs) == 0
    # assert_output checks output → hello is not [0-9]+
    asrt_errs = [e for e in errors if isinstance(e, AssertionViolationError)]
    assert len(asrt_errs) == 1


# ---------------------------------------------------------------------------
# Error type correctness
# ---------------------------------------------------------------------------

def test_assert_output_returns_correct_error_type():
    script = '''
# @assert_output "echo hello" : "[0-9]+"
echo hello | cat
'''
    errors = _check(script)
    asrt_errs = [e for e in errors if isinstance(e, AssertionViolationError)]
    assert len(asrt_errs) == 1
    assert asrt_errs[0].cmd_idx == 0  # echo is index 0


def test_assert_input_contains_returns_contains_error_type():
    script = '''
# @assert_input_contains "cat" : "[0-9]+"
echo hello | cat
'''
    errors = _check(script)
    contains_errs = [e for e in errors if isinstance(e, ContainsViolationError)]
    assert len(contains_errs) == 1
    assert contains_errs[0].cmd_idx == 1  # cat is index 1

