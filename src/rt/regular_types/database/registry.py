import importlib
import importlib.resources
import json
import pkgutil
import re
import sys
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path

import yaml
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver, TypeResolver, build_env
from rt.regular_types.stream_transform import Constant, StreamTransform
from rt.regular_types.stream_type import StreamType
from rt.type_checking.annotations import (
    CommandAnnotation,
    EnvAnnotation,
    EnvAnnotationKind,
)

_cache: dict[str, TypeResolver] = {}
_loaded = False


def get_type(
    invocation: CommandInvocationInitial,
    user_annotations: Sequence[CommandAnnotation] | None = None,
    env_annotations: Mapping[str, Sequence[EnvAnnotation]] | None = None,
    heuristic_rules: Sequence[str] | None = None,
) -> CommandType:
    if not _loaded:
        _populate_cache()

    key = _cache_key(invocation)
    resolver = _cache.get(key)

    if resolver is None:
        resolver = RuleResolver()

    env = build_env(invocation)
    if env_annotations:
        env = _enrich_env(env, invocation, env_annotations)

    return resolver.resolve(
        invocation,
        user_annotations or [],
        env,
        heuristic_rules,
    )


def register_type(key: str, resolver: RuleResolver) -> None:
    d = _user_basic_dir()
    if d is None:
        print(
            "rt: platformdirs not available, type not persisted",
            file=sys.stderr,
        )
        return

    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{key}.yaml"
    with open(path, "w") as f:
        yaml.dump(
            _resolver_to_yaml_data(resolver),
            f,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )

    _cache[key] = resolver


# ---------------------------------------------------------------------------
# Discovery & loading
# ---------------------------------------------------------------------------


def _load_yaml_resolvers() -> dict[str, RuleResolver]:
    resolvers: dict[str, RuleResolver] = {}
    database = importlib.resources.files("rt.regular_types.database.basic")
    for entry in database.iterdir():
        if not entry.name.endswith(".yaml"):
            continue
        key = entry.name.removesuffix(".yaml")
        with entry.open("r") as f:
            data = yaml.safe_load(f)
        resolvers[key] = RuleResolver(
            input_type=data.get("input", ".*"),
            output_type=data.get("output", ".*"),
            when=data.get("when"),
        )
    return resolvers


def _load_extended_resolvers() -> dict[str, TypeResolver]:
    import rt.regular_types.database.extended as pkg

    resolvers: dict[str, TypeResolver] = {}
    for _, mod_name, is_pkg in pkgutil.iter_modules(pkg.__path__):
        if mod_name.startswith("_") or is_pkg:
            continue
        mod = importlib.import_module(f"rt.regular_types.database.extended.{mod_name}")
        factory = getattr(mod, "resolve", None)
        if factory is not None:
            resolvers[mod_name] = factory()
    return resolvers


def _user_basic_dir() -> Path | None:
    try:
        from platformdirs import user_data_path
    except ImportError:
        return None
    return user_data_path("rt") / "types"


def _load_user_yaml_resolvers() -> dict[str, RuleResolver]:
    d = _user_basic_dir()
    if d is None or not d.exists():
        return {}

    resolvers: dict[str, RuleResolver] = {}
    for path in sorted(d.glob("*.yaml")):
        key = path.stem
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(
                f"rt: skipping malformed user type {path.name}: {e}",
                file=sys.stderr,
            )
            continue

        if not isinstance(data, dict):
            print(
                f"rt: skipping {path.name}: expected a mapping, got {type(data).__name__}",
                file=sys.stderr,
            )
            continue

        try:
            resolvers[key] = RuleResolver(
                input_type=data.get("input", ".*"),
                output_type=data.get("output", ".*"),
                when=data.get("when"),
            )
        except Exception as e:
            print(
                f"rt: skipping {path.name}: {e}",
                file=sys.stderr,
            )
            continue

    return resolvers


def _populate_cache() -> None:
    global _cache, _loaded
    if _loaded:
        return

    yaml_resolvers = _load_yaml_resolvers()
    extended_resolvers = _load_extended_resolvers()
    user_resolvers = _load_user_yaml_resolvers()

    _cache.update(yaml_resolvers)
    _cache.update(extended_resolvers)
    _cache.update(user_resolvers)

    _loaded = True


# ---------------------------------------------------------------------------
# Invocation -> cache key resolution
# ---------------------------------------------------------------------------


def _cache_key(invocation: CommandInvocationInitial) -> str:
    if invocation.cmd_name == "xargs":
        sub = _extract_xargs_subcommand(invocation)
        if sub is not None:
            return f"xargs_{sub}"
    return invocation.cmd_name


def _extract_xargs_subcommand(invocation: CommandInvocationInitial) -> str | None:
    """Return the subcommand that *xargs* will execute, if any.

    Walks the operand list skipping flag options and their arguments
    (``-I``/``--replace``, ``-d``/``--delimiter``, ``-L``/``--max-lines``)
    to find the first non-flag operand, which is the subcommand name.
    Returns ``None`` if no subcommand is present.
    """
    operands = [op.name for op in invocation.operand_list]
    flags = {fo.get_name() for fo in invocation.flag_option_list}
    index = 0

    while index < len(operands):
        operand = operands[index]
        if operand == "-I" or operand == "--replace":
            index += 1
            continue
        if operand.startswith("-I"):
            index += 1
            continue
        if operand.startswith("-") or operand.startswith("--"):
            index += 1
            if (
                operand == "-d"
                or operand == "--delimiter"
                or operand == "-L"
                or operand == "--max-lines"
            ):
                index += 1
            continue
        if index == 0 and operand.startswith("-"):
            break
        while index < len(operands) and (
            operands[index] in flags or operands[index].startswith("-")
        ):
            index += 1
        if index < len(operands):
            return operands[index]
        break

    return None


# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------


def _enrich_env(
    env: MutableMapping[str, StreamTransform],
    invocation: CommandInvocationInitial,
    env_annotations: Mapping[str, Sequence[EnvAnnotation]],
) -> dict[str, StreamTransform]:
    for i, op in enumerate(invocation.operand_list, 1):
        for annot in env_annotations.get(op.name, []):
            if annot.kind in {EnvAnnotationKind.FILE, EnvAnnotationKind.CONCRETIZE}:
                env[f"@${i}"] = Constant(StreamType.from_pattern(annot.regex))
    return dict(env)


# ---------------------------------------------------------------------------
# YAML serialization
# ---------------------------------------------------------------------------


def _resolver_to_yaml_data(resolver: RuleResolver) -> dict:
    data: dict = {
        "input": resolver._input,
        "output": resolver._output,
    }
    if resolver._when:
        data["when"] = resolver._when
    return data


# ---------------------------------------------------------------------------
# Type alias management
# ---------------------------------------------------------------------------

_BUILTIN_TYPE_ALIASES: dict[str, str] = {
    "filename": r"[^/\n]+",
    "mask": r"[rwx-]{9}",
    "base64": r"(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?",
    "integer": r"-?[0-9]+",
    "float": r"-?(?:[0-9]+\.[0-9]*|\.[0-9]+)",
    "md5": r"[A-Fa-f0-9]{32}",
    "sha128": r"[A-Fa-f0-9]{32}",
    "sha256": r"[A-Fa-f0-9]{64}",
    "number": r"-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)",
    "day-of-the-week": r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon|Tue|Wed|Thu|Fri|Sat|Sun)",
    "month": r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
    "hh:mm:ss": r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]",
    "year": r"[0-9]{4}",
    "username": r"[a-z_][a-z0-9_-]*",
    "hh:mm": r"(?:[01][0-9]|2[0-3]):[0-5][0-9]",
    "absolute-path": r"/.*",
    "ip-address": r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}",
}


def _alias_file() -> Path | None:
    d = _user_basic_dir()
    if d is None:
        return None
    return d / "aliases.json"


def _load_aliases() -> dict[str, str]:
    path = _alias_file()
    if path is None or not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_alias(name: str, expression: str) -> None:
    aliases = _load_aliases()
    aliases[name] = expression
    path = _alias_file()
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(aliases, f, indent=4)


def get_type_name(type_exp: str) -> str | None:
    match = re.fullmatch(r"\[\[:([A-Za-z0-9_-]+):\]\]", type_exp)
    if match:
        return match.group(1)
    return None


def resolve_type_from_name(type_name: str) -> str | None:
    if type_name in _BUILTIN_TYPE_ALIASES:
        return _BUILTIN_TYPE_ALIASES[type_name]
    aliases = _load_aliases()
    if type_name in aliases:
        return aliases[type_name]
    return None
