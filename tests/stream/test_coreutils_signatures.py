from pathlib import Path

from pash_annotations.datatypes.BasicDatatypes import Operand
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from stream.command_signature import InferenceResult
from stream.regular_type import RegularType
from stream.signature_loader import SignatureLoader

GNU_COREUTILS_COMMANDS = {
    "[",
    "arch",
    "b2sum",
    "base32",
    "base64",
    "basename",
    "basenc",
    "cat",
    "chcon",
    "chgrp",
    "chmod",
    "chown",
    "chroot",
    "cksum",
    "comm",
    "cp",
    "csplit",
    "cut",
    "date",
    "dd",
    "df",
    "dir",
    "dircolors",
    "dirname",
    "du",
    "echo",
    "env",
    "expand",
    "expr",
    "factor",
    "false",
    "fmt",
    "fold",
    "groups",
    "head",
    "hostid",
    "id",
    "install",
    "join",
    "kill",
    "link",
    "ln",
    "logname",
    "ls",
    "md5sum",
    "mkdir",
    "mkfifo",
    "mknod",
    "mktemp",
    "mv",
    "nice",
    "nl",
    "nohup",
    "nproc",
    "numfmt",
    "od",
    "paste",
    "pathchk",
    "pinky",
    "pr",
    "printenv",
    "printf",
    "ptx",
    "pwd",
    "readlink",
    "realpath",
    "rm",
    "rmdir",
    "runcon",
    "sha1sum",
    "sha224sum",
    "sha256sum",
    "sha384sum",
    "sha512sum",
    "shred",
    "shuf",
    "sleep",
    "sort",
    "split",
    "stat",
    "stdbuf",
    "stty",
    "sum",
    "sync",
    "tac",
    "tail",
    "tee",
    "test",
    "timeout",
    "touch",
    "tr",
    "true",
    "truncate",
    "tsort",
    "tty",
    "uname",
    "unexpand",
    "uniq",
    "unlink",
    "uptime",
    "users",
    "vdir",
    "wc",
    "who",
    "whoami",
    "yes",
}


def _load_signatures():
    SignatureLoader.reset_instance()
    return SignatureLoader.get_instance("./src/stream/signatures")


def test_independent_coreutils_yaml_signatures_match_paper_claim():
    loader = _load_signatures()
    signature_names = {signature.command_name for signature in loader.signatures}
    yaml_names = {path.stem for path in Path("src/stream/signatures").glob("*.yaml")}
    supported_coreutils = GNU_COREUTILS_COMMANDS & yaml_names
    xargs_signatures = {
        name for name in yaml_names if name == "xargs" or name.startswith("xargs_")
    }

    assert len(GNU_COREUTILS_COMMANDS) == 106
    assert supported_coreutils <= signature_names
    assert len(supported_coreutils) == 106
    assert xargs_signatures.isdisjoint(GNU_COREUTILS_COMMANDS)


def test_coreutils_identity_filters_preserve_line_type(lookup_signature, apply_signature):
    tee_signature = lookup_signature("tee")
    input_type = RegularType("[a-z]+")

    result = apply_signature(
        tee_signature,
        input_type,
        CommandInvocationInitial("tee", [], []),
    )

    assert isinstance(result, InferenceResult)
    assert result.output_type.is_subtype(input_type)[0]
    assert input_type.is_subtype(result.output_type)[0]

    source_result = apply_signature(
        tee_signature,
        RegularType(""),
        CommandInvocationInitial("tee", [], []),
    )

    assert isinstance(source_result, InferenceResult)
    assert RegularType("[a-z]+").is_subtype(source_result.output_type)[0]
    assert source_result.self_contained is False


def test_coreutils_file_operands_fall_back_to_unknown_content(lookup_signature, apply_signature):
    tac_signature = lookup_signature("tac")

    result = apply_signature(
        tac_signature,
        RegularType(""),
        CommandInvocationInitial("tac", [], [Operand("/tmp/input.txt")]),
    )

    assert isinstance(result, InferenceResult)
    assert RegularType("[a-z]+").is_subtype(result.output_type)[0]
    assert result.self_contained is False


def test_coreutils_stable_output_shapes_and_no_stdin_heuristic(lookup_signature, apply_signature):
    nproc_signature = lookup_signature("nproc")
    whoami_signature = lookup_signature("whoami")

    nproc_result = apply_signature(
        nproc_signature,
        RegularType(".*"),
        CommandInvocationInitial("nproc", [], []),
    )
    whoami_input, no_input_type = whoami_signature.get_input_type(
        CommandInvocationInitial("whoami", [], []),
        ["no_ignored_input"],
        {},
    )

    assert isinstance(nproc_result, InferenceResult)
    assert nproc_result.output_type.is_subtype(RegularType("[0-9]+"))[0]
    assert whoami_input.pattern == ""
    assert no_input_type is None
