import re
from abc import ABC, abstractmethod
from collections.abc import Mapping, MutableMapping, Sequence

from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

from rt.regex import parse_regex
from rt.regular_types.command_type import CommandType
from rt.regular_types.stream_transform import Constant, Input, Regex, StreamTransform
from rt.regular_types.stream_type import StreamType
from rt.type_checking.annotations import CommandAnnotation, CommandAnnotationKind, EnvAnnotation


class TypeResolver(ABC):
    @abstractmethod
    def resolve(
        self,
        invocation: CommandInvocationInitial,
        annotations: Sequence[CommandAnnotation] | None,
        env: Mapping[str, StreamTransform],
        heuristic_rules: Sequence[str] | None = None,  # TODO: Should this field be removed since heuristics now live outside yaml or should heuristics move back into yaml?
    ) -> CommandType:
        pass


def _parse_transform_expression(
    expression: str, env: Mapping[str, StreamTransform]
) -> StreamTransform:
    # The expression language is documented in docs/command-signatures.md.
    if not expression:
        return Input()

    stripped = expression.strip()

    hole_match = re.fullmatch(r"\{\{\s*([^{}]+?)\s*\}\}", stripped)
    if hole_match:
        hole_name = hole_match.group(1)
        if hole_name in env:
            return env[hole_name]
        if hole_name.startswith("@@"):
            inner = hole_name[2:]
            if inner in env:
                return env[inner]
            return _parse_transform_expression(inner, env)
        if hole_name.startswith("@"):
            inner = hole_name[1:]
            if inner in env:
                return env[inner]
            return _parse_transform_expression(inner, env)
        raise ValueError(f"Unknown hole reference: {hole_name}")

    return Regex(parse_regex(stripped))


def resolve_annotation_pattern(
    pattern: str,
    env: Mapping[str, StreamTransform],
    input: StreamType | None = None,
) -> StreamType:
    """Resolve an annotation regex that may contain ``{{hole}}`` references.

    Uses the same resolution path as YAML output expressions.  If the pattern
    is a plain regex it is compiled directly; if it is a ``{{hole}}`` reference
    the corresponding env transform is evaluated.

    .. note::
        Mixed patterns like ``prefix{{input}}suffix`` produce a ``Regex``
        transform whose AST may contain holes.  When StreamTypeTemplate is
        wired up the call to ``StreamType.from_regex`` below will be replaced
        with ``StreamTypeTemplate.from_regex(…).instantiate(input)`` so that
        those holes are properly resolved.
    """
    transform = _parse_transform_expression(pattern, env)
    return transform.apply(input or StreamType.from_pattern(".*"), {})


def build_command_env(
    invocation: CommandInvocationInitial,
    env_annotations: Mapping[str, Sequence[EnvAnnotation]] | None = None,
) -> dict[str, StreamTransform]:
    env = build_env(invocation)
    if env_annotations:
        env = _enrich_env(env, invocation, env_annotations)
    return env


def build_env(invocation: CommandInvocationInitial) -> dict[str, StreamTransform]:
    env: dict[str, StreamTransform] = {"input": Input()}
    operands = [op.name for op in invocation.operand_list]
    for i, val in enumerate(operands, 1):
        env[f"${i}"] = Constant(StreamType.from_pattern(re.escape(val)))
        env[f"@${i}"] = Constant(StreamType.from_pattern(".*"))
        env[f"@@${i}"] = Constant(StreamType.from_pattern(".*"))
    if operands:
        joined = " ".join(re.escape(op) for op in operands)
        env["$@"] = Constant(StreamType.from_pattern(joined))
    else:
        env["$1"] = Constant(StreamType.from_pattern(".*"))
        env["@$1"] = Constant(StreamType.from_pattern(".*"))
        env["@@$1"] = Constant(StreamType.from_pattern(".*"))
        env["$@"] = Constant(StreamType.from_pattern(".*"))

    option_args: dict[str, list[str]] = {}
    for fo in invocation.flag_option_list:
        arg = getattr(fo, "option_arg", None)
        if arg is not None:
            name = fo.get_name().lstrip("-")
            option_args.setdefault(name, []).append(arg)

    for opt_name, args in option_args.items():
        for i, arg in enumerate(args, 1):
            env[f"{opt_name}${i}"] = Constant(
                StreamType.from_pattern(re.escape(arg))
            )
        env[f"{opt_name}$@"] = Constant(
            StreamType.from_pattern(" ".join(re.escape(a) for a in args))
        )

    return env


def _enrich_env(
    env: MutableMapping[str, StreamTransform],
    invocation: CommandInvocationInitial,
    env_annotations: Mapping[str, Sequence[EnvAnnotation]],
) -> dict[str, StreamTransform]:
    for i, op in enumerate(invocation.operand_list, 1):
        for annot in env_annotations.get(op.name, []):
            if annot.kind in {EnvAnnotationKind.FILE, EnvAnnotationKind.CONCRETIZE}:
                env[f"@${i}"] = Constant(StreamType.from_pattern(annot.regex))
    for name, anns in env_annotations.items():
        for ann in anns:
            if ann.kind == EnvAnnotationKind.VAR:
                env[f"var:{name}"] = Constant(
                    StreamType(
                        automaton=StreamType.from_pattern(ann.regex).automaton,
                        regex=ann.regex,
                    )
                )
    return dict(env)


class RuleResolver(TypeResolver):
    def __init__(
        self,
        input_type: str = ".*",
        output_type: str = ".*",
        when: list[dict] | None = None,
    ):
        self._input = input_type
        self._output = output_type
        self._when = when or []

    def resolve(
        self,
        invocation: CommandInvocationInitial,
        annotations: Sequence[CommandAnnotation] | None,
        env: Mapping[str, StreamTransform],
        heuristic_rules: Sequence[str] | None = None,
    ) -> CommandType:
        annotations = annotations or []

        for annotation in reversed(annotations):
            if annotation.kind == CommandAnnotationKind.ASSUME_OUTPUT:
                input_st = (
                    StreamType.from_pattern(self._input)
                    if self._input
                    else StreamType.from_pattern("")
                )
                transform = _parse_transform_expression(annotation.regex, env)
                return CommandType(input_st, transform)

        flags = {fo.get_name() for fo in invocation.flag_option_list}
        input_pat, output_pat = self._match_when(flags)

        transform = _parse_transform_expression(output_pat, env)

        accepted_input = (
            StreamType.from_pattern(input_pat)
            if input_pat
            else StreamType.from_pattern("")
        )
        return CommandType(accepted_input, transform)

    def _match_when(self, invocation_flags: set[str]) -> tuple[str, str]:
        for entry in self._when:
            required = set(entry.get("opts", entry.get("flags", [])))
            if required.issubset(invocation_flags):
                return (
                    entry.get("input", self._input),
                    entry.get("output", self._output),
                )
        return self._input, self._output

    def _get_operands(
        self,
        invocation: CommandInvocationInitial,
    ) -> list[str]:
        return [op.name for op in invocation.operand_list]

    def _file_from_env(
        self,
        env: dict[str, StreamTransform],
    ) -> StreamType:
        for i in range(10, 0, -1):
            key = f"@${i}"
            if key in env:
                return env[key].apply(StreamType.from_pattern(".*"), {})
        return StreamType.from_pattern(".*")
