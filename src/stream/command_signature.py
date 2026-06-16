from dataclasses import dataclass
import logging
from stream.command_type import CommandType, CommandTypeResult, PolymorphicCommandType, SimpleCommandType
from stream.regular_type import RegularType
from stream.transformation_ast import ALPHA, ConstantTransform, TransformationNode, regex_ast_to_transform_node
import re
from typing import Callable, List, Dict, Any, Optional, Tuple
from shasta.ast_node import *
from pash_annotations.parser.parser import parse as annot_parse
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from dk.brics.automaton import Automaton # type: ignore
from stream.tool_error import ToolError, PashAnnotationParsingError
from stream.user_annotation import AnnotationType, EnvAnnotation, UserAnnotation


def annotation_pattern_mentions_newline(pattern: str) -> bool:
    return "\n" in pattern or "\\n" in pattern or "\\012" in pattern


@dataclass
class InferenceResult:
    output_type: RegularType
    backward_func: Optional[Callable[[Automaton], Automaton]] = None
    self_contained: Optional[bool] = None


class CommandSignature:
    def __init__(
        self, 
        command_name: str, 
        default_input_type: str, 
        default_output_type: str, 
        args: List[Dict[str, Any]], 
        flags: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
        isInteresting: bool,
        isTainted: bool
    ) -> None:
        self.command_name = command_name
        self.default_input_type = RegularType(default_input_type)
        self.default_output_type = RegularType(default_output_type)
        self.args = args
        self.flags = flags
        self.rules = rules
        self.isInteresting = isInteresting
        self.isTainted = isTainted
    def matches_command(self, command_invocation: CommandInvocationInitial) -> bool:
        assert isinstance(command_invocation, CommandInvocationInitial)
        if command_invocation.cmd_name == self.command_name:
            return True
        if command_invocation.cmd_name == "xargs":
            xargs_command = self._get_xargs_command(command_invocation)
            if xargs_command is None:
                return False
            if "xargs_" + xargs_command == self.command_name:
                return True
        return False

    @staticmethod
    def _get_xargs_command(command_invocation: CommandInvocationInitial) -> Optional[str]:
        operands = [operand.name for operand in command_invocation.operand_list]
        index = 0

        while index < len(operands):
            operand = operands[index]
            if operand == "--":
                index += 1
                break
            if operand in {"-0", "-r", "--null", "--no-run-if-empty"}:
                index += 1
                continue
            if operand in {"-d", "-E", "-e", "-I", "-i", "-L", "-l", "-n", "-P", "-s", "--delimiter", "--eof", "--replace", "--max-lines", "--max-args", "--max-procs", "--max-chars"}:
                index += 2
                continue
            if (
                re.match(r"^-(d|E|e|I|i|L|l|n|P|s).+", operand)
                or operand.startswith("--delimiter=")
                or operand.startswith("--eof=")
                or operand.startswith("--replace=")
                or operand.startswith("--max-lines=")
                or operand.startswith("--max-args=")
                or operand.startswith("--max-procs=")
                or operand.startswith("--max-chars=")
            ):
                index += 1
                continue
            if operand.startswith("-"):
                index += 1
                continue
            return operand

        return operands[index] if index < len(operands) else None

    @staticmethod
    def _xargs_uses_explicit_delimiter(command_invocation: CommandInvocationInitial) -> bool:
        if command_invocation.cmd_name != "xargs":
            return False

        operands = [operand.name for operand in command_invocation.operand_list]
        flags = {flag_option.get_name() for flag_option in command_invocation.flag_option_list}
        return bool(
            {"-0", "--null"} & set(operands)
            or {"-0", "--null", "-d", "--delimiter"} & flags
            or any(operand.startswith("-d") and operand != "-d" for operand in operands)
        )
    
    def determine_command_type(self, parsed_command_invocation: CommandInvocationInitial, user_annotations: List[UserAnnotation], env_annotations: Dict[str, List[EnvAnnotation]]) -> CommandType:
        for annotation in user_annotations:
            if annotation.annotation_type == AnnotationType.ASSUME:
                repr_mode = "stream" if annotation_pattern_mentions_newline(annotation.pattern) else "line"
                return SimpleCommandType(
                    RegularType(".*"),
                    RegularType(annotation.pattern, repr_mode=repr_mode, tainted=False),
                    self_contained=True,
                )

        if parsed_command_invocation.cmd_name != "xargs" and parsed_command_invocation.cmd_name != "grep" and len(parsed_command_invocation.operand_list) >= 1 and self.isInteresting:
            operand = parsed_command_invocation.operand_list[0].name
            if operand.startswith("-"):
                logging.debug(
                    "Treating leading operand %r for %s as parser-normalized input instead of a fatal annotation error",
                    operand,
                    parsed_command_invocation.cmd_name,
                )

        flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
        if "--version" in flags or "--help" in flags:
            return SimpleCommandType(RegularType(".*"), RegularType(".*"), self_contained=True)
        return self._finalize_command_type(
            self.construct_command_type(parsed_command_invocation, env_annotations),
            parsed_command_invocation,
        )

    def _finalize_command_type(
        self,
        command_type: CommandType,
        parsed_command_invocation: CommandInvocationInitial,
    ) -> CommandType:
        if (
            isinstance(command_type, PolymorphicCommandType)
            and command_type.normalize_input_to_line is None
        ):
            command_type.normalize_input_to_line = parsed_command_invocation.cmd_name not in [
                "cut",
                "tr",
                "grep",
                "head",
                "tail",
            ]
        return command_type

    def construct_command_type(self, parsed_command_invocation: CommandInvocationInitial, env_annotations: Dict[str, List[EnvAnnotation]]) -> CommandType:
        output_transform, self_contained, tainted = self.construct_output_transform(
            parsed_command_invocation,
            env_annotations,
        )
        normalize_input_to_line = parsed_command_invocation.cmd_name not in ["cut", "tr", "grep", "head", "tail"]
        return PolymorphicCommandType(
            output_transform,
            self_contained=self_contained,
            normalize_input_to_line=normalize_input_to_line,
            output_tainted=tainted,
        )

    def apply_command_type(self, command_type: CommandType, input_type: RegularType) -> InferenceResult:
        result: CommandTypeResult = command_type.apply_to_input(input_type)
        return InferenceResult(result.output_type, result.backward_func, result.self_contained)

    def construct_output_transform(
        self,
        parsed_command_invocation: CommandInvocationInitial,
        env_annotations: Dict[str, List[EnvAnnotation]],
    ) -> Tuple[TransformationNode, bool, bool]:
        lose_precision = True
        self_contained = True
        tainted = self.isTainted

        env_related_command_names = {
            "arch",
            "chroot",
            "date",
            "df",
            "dir",
            "dircolors",
            "docker",
            "du",
            "groups",
            "hostid",
            "hostname",
            "id",
            "logname",
            "ls",
            "mktemp",
            "nice",
            "nohup",
            "nproc",
            "pinky",
            "printenv",
            "ps",
            "pwd",
            "readlink",
            "realpath",
            "runcon",
            "stat",
            "stdbuf",
            "stty",
            "timeout",
            "tty",
            "uname",
            "uptime",
            "users",
            "vdir",
            "who",
            "whoami",
            "curl",
        }
        if parsed_command_invocation.cmd_name in env_related_command_names:
            self_contained = False

        env: Dict[str, TransformationNode] = {}

        for i, arg_info in enumerate(self.args):
            arg_name: str = arg_info["name"]
            is_regex: bool = arg_info.get("is_regex", False)
            if i >= len(parsed_command_invocation.operand_list):
                continue

            arg = parsed_command_invocation.operand_list[i].name

            file_content = self._annotated_content_type(arg, env_annotations)
            if file_content is not None:
                env[f"{arg_name}.content"] = ConstantTransform(file_content)
                lose_precision = False
                tainted = False
            else:
                env[f"{arg_name}.content"] = ConstantTransform(RegularType(".*"))
                lose_precision = True
                tainted = True
                self_contained = False

            pattern, variable_self_contained, variable_precise = self._argument_pattern(
                arg,
                is_regex,
                env_annotations,
            )
            env[arg_name] = ConstantTransform(RegularType(pattern))
            if not variable_self_contained:
                self_contained = False
            if variable_precise:
                lose_precision = False
                tainted = False

        env["actual_input_type"] = ALPHA
        env["output_type"] = ConstantTransform(self.default_output_type)

        parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
        parsed_args = set(env.keys())

        for rule in self.rules:
            required_flags = set(rule["condition"].get("flags", []))
            required_args = set(rule["condition"].get("args", []))
            no_flags = set(rule["condition"].get("no_flags", []))
            no_args = set(rule["condition"].get("no_args", []))

            if (
                required_flags.issubset(parsed_flags)
                and required_args.issubset(parsed_args)
                and not any(flag in parsed_flags for flag in no_flags)
                and not any(arg in parsed_args for arg in no_args)
            ):
                update_variables: Dict[str, str] = rule.get("update", {}).copy()
                logging.debug(f"Command: {self.command_name}, Rule: {rule['condition']} -> {rule['update']}")
                for key, value in update_variables.items():
                    try:
                        env[key] = self._build_transform(value, env)
                    except Exception:
                        raise ToolError(f"Error in updating env for command, missing argument when updating {key} with {value}")
                logging.debug(f"Command: {self.command_name}, Updated AST env: {env}")
                if rule.get("output_tainted", tainted):
                    tainted = rule.get("output_tainted", tainted)
                    lose_precision = tainted
                if rule.get("stop", False):
                    break

        logging.debug(f"Command: {self.command_name}, Output AST (if compatible): {env['output_type']}")
        logging.debug("-"*60)
        return env["output_type"], self_contained, tainted

    def _annotated_content_type(
        self,
        arg: str,
        env_annotations: Dict[str, List[EnvAnnotation]],
    ) -> Optional[RegularType]:
        for annot in env_annotations.get(arg, []):
            if annot.annotation_type in {AnnotationType.FILE, AnnotationType.CONCRETIZE}:
                return RegularType(annot.pattern)
        return None

    def _argument_pattern(
        self,
        arg: str,
        is_regex: bool,
        env_annotations: Dict[str, List[EnvAnnotation]],
    ) -> Tuple[str, bool, bool]:
        parts = []
        last_end = 0
        self_contained = True
        precise = False

        for var_match in re.finditer(r"(\$\{.*?\})", arg):
            if var_match.start() > last_end:
                text = arg[last_end:var_match.start()]
                parts.append(re.escape(text) if not is_regex else text)

            var_name = var_match.group(1)
            var_pattern = ".*"
            matched = False
            for annot in env_annotations.get(var_name, []):
                if annot.annotation_type == AnnotationType.VAR:
                    var_pattern = annot.pattern
                    precise = True
                    matched = True
                    break
            if not matched:
                self_contained = False
            parts.append(var_pattern)
            last_end = var_match.end()

        if last_end < len(arg):
            text = arg[last_end:]
            parts.append(re.escape(text) if not is_regex else text)

        if parts:
            return "".join(parts), self_contained, precise
        return re.escape(arg) if not is_regex else arg, self_contained, precise

    def _build_transform(self, value: str | RegularType | TransformationNode, env: Dict[str, TransformationNode]) -> TransformationNode:
        if isinstance(value, TransformationNode):
            return value
        if isinstance(value, RegularType):
            return ConstantTransform(value)
        if not isinstance(value, str):
            return ConstantTransform(RegularType(str(value)))

        exact_hole = re.fullmatch(r"\{\{([^{}]+)\}\}", value)
        if exact_hole is not None:
            hole_name = exact_hole.group(1)
            if hole_name in env:
                return env[hole_name]

        from stream.regex_parser import RegexParser

        return regex_ast_to_transform_node(RegexParser(value).parse(), env)

    def process_stream_input(self, previous_output_type: RegularType) -> Tuple[RegularType, bool]:
        if previous_output_type.repr_mode == "stream":
            return previous_output_type.to_line_based_repr(), True
        return previous_output_type, False


    def get_operands(self, parsed_command_node: CommandInvocationInitial) -> List[str]:
        assert isinstance(parsed_command_node, CommandInvocationInitial)
        operand_list = parsed_command_node.operand_list.copy()
        if len(operand_list) == 0:
            return []
        if parsed_command_node.cmd_name == "xargs":
            return [operand.name for operand in operand_list[1:]]
        return [operand.name for operand in operand_list]


    def get_file_name(self, parsed_command_invocation: CommandInvocationInitial, env_annotations: Dict[str, List[EnvAnnotation]]) -> RegularType:
        file_name = parsed_command_invocation.operand_list[-1].name
        for annotation in env_annotations.get(file_name, []):
            if annotation.annotation_type in {AnnotationType.FILE, AnnotationType.CONCRETIZE}:
                return RegularType(annotation.pattern, tainted=False)
        return RegularType(".*")
    
    def determine_input_type(self, parsed_command_invocation: CommandInvocationInitial, user_annotations: List[UserAnnotation], heuristic_rules: List[str], env_annotations: Dict[str, List[EnvAnnotation]]) -> Tuple[RegularType, Optional[RegularType]]:
        assert isinstance(parsed_command_invocation, CommandInvocationInitial)

        for annotation in user_annotations:
            if annotation.annotation_type == AnnotationType.EXPECT:
                return RegularType(annotation.pattern), None

        if self._xargs_uses_explicit_delimiter(parsed_command_invocation):
            heuristic_rules = [rule for rule in heuristic_rules if rule != "no_space_in_file_name"]
            
        return self.get_input_type(parsed_command_invocation, heuristic_rules, env_annotations)
    
    def get_input_type(self, parsed_command_invocation: CommandInvocationInitial, heuristic_rules: List[str], env_annotations: Dict[str, List[EnvAnnotation]]) -> Tuple[RegularType, Optional[RegularType]]:

        input_type = self.default_input_type.pattern

        no_input_type = None

        parsed_args = set(map(lambda arg: arg['name'], self.args[:len(self.get_operands(parsed_command_invocation))]))

        parsed_flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))

        heuristic_rules = set(heuristic_rules)

        for rule in self.rules: # iterate over all rules, from top to bottom
            required_flags = set(rule['condition'].get('flags', []))
            required_args = set(rule['condition'].get('args', []))
            no_flags = set(rule['condition'].get('no_flags', []))
            no_args = set(rule['condition'].get('no_args', []))
            required_heuristics = set(rule['condition'].get('heuristics', []))

            # match the rule, required flags and args are subset of actual flags and args, and no_flags and no_args are not in actual flags and args
            if (required_flags.issubset(parsed_flags) and
                required_args.issubset(parsed_args) and
                not any(flag in parsed_flags for flag in no_flags) and
                not any(arg in parsed_args for arg in no_args) and
                required_heuristics.issubset(heuristic_rules)):

                # update input type
                update_variables: Dict[str, str] = rule.get('update', {}).copy()
                for key, value in update_variables.items():
                    if key == 'input_type':
                        input_type = value
                    if key == "no_input_type":
                        no_input_type = value
                logging.debug(f"Command: {self.command_name}, Updated input type: {input_type}")
                if rule.get('stop', False):
                    break

        logging.debug(f"Command: {self.command_name}, Expected input type: {input_type}")
        
        return RegularType(input_type), RegularType(no_input_type) if no_input_type is not None else None
    
    def __repr__(self) -> str:
        return f"CommandSignature({self.command_name}, {self.default_input_type}, {self.default_output_type}, {self.args}, {self.flags}, {self.rules})"
