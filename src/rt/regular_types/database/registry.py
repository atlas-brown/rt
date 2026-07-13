import importlib
import importlib.resources
import pkgutil
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
            output_type=data.get("output", "{{input}}"),
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
                output_type=data.get("output", "{{input}}"),
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
