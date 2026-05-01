import logging
import re
import time
import traceback
from dataclasses import dataclass
from stream.command_signature import CommandSignature, InferenceResult
from stream.config.global_config import CONFIG
from stream.regular_type import RegularType
from stream.parser.shell_parser import ShellParser
from typing import Callable, Dict, Optional, List, Tuple
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from stream.tool_error import ToolError, PashAnnotationParsingError
from stream.user_annotation import AnnotationType, EnvAnnotation, UserAnnotation
from stream.utils.format import pretty_ast_node
from shasta.ast_node import PipeNode, CommandNode
from stream.utils.function_timer import timer


def pattern_mentions_newline(pattern: str) -> bool:
    return "\n" in pattern or "\\n" in pattern or "\\012" in pattern


def automata_size_for_statistics(regular_type: RegularType) -> int:
    """Count states in line-based form without changing checker semantics."""
    if regular_type.repr_mode == "stream" and CONFIG.get("enable_FST", True):
        regular_type = regular_type.to_line_based_repr()
        regular_type.nfa.setDeterministic(False)
        regular_type.nfa.determinize()
        regular_type.nfa.removeDeadTransitions()
        regular_type.nfa.minimize()
    return len(regular_type.nfa.getStates())


@dataclass
class ErrorResult:
    """Represents a type checking error found during pipeline analysis.
    
    Each instance represents a discovered error. All fields have default values.
    """
    message: Optional[str] = None
    witness: Optional[str] = None
    derivation_trace: Optional[List[str]] = None
    all_input: Optional[bool]= None
    serious_violation: Optional[bool] = None
    command_name: Optional[str] = None
    tainted: Optional[bool] = None
    better_witness: Optional[Tuple[str, int]] = None
    command_index: Optional[int] = None


@dataclass
class CheckingResult:
    error_results: List[ErrorResult]
    self_contained: bool
    pipeline_content: str
    pipeline_length: int
    max_automata_size: int
    statistics_time: float = 0.0
    runtime_error_kind: Optional[str] = None
    runtime_error_message: Optional[str] = None
    runtime_error_type: Optional[str] = None
    runtime_error_traceback: Optional[str] = None


class ScriptChecker:
    def __init__(self, 
                 pipeline_address: str, 
                 enable_user_annotations: bool = True,
                 enable_rule_no_empty_output: bool = True,
                 enable_rule_no_ignored_input: bool = True,
                 enable_rule_no_meaningless_command = True,
                 enable_rule_no_sort_non_numeric_with_numeric_input = True,
                 enable_stage_timeout: bool = False,
                 stage_timeout: int = 10,
                 check_all_pipelines: bool = True,
                 label: bool = True,
                 enable_detailed_error_reporting: bool = True,
                 enable_concretization: bool = True
        ) -> None:
        self.pipelines = None
        self.pipeline_nodes = None
        self.current_index = 0
        self.enable_stage_timeout = enable_stage_timeout
        self.stage_timeout = stage_timeout
        self.enable_user_annotations = enable_user_annotations
        self.check_all_pipelines = check_all_pipelines
        self.label = label
        self.pipeline_address = pipeline_address
        self.heuristic_rules: List[str] = []
        self.enable_detailed_error_reporting = enable_detailed_error_reporting

        self.heuristic_rules.append("no_space_in_file_name")

        if enable_rule_no_ignored_input:
            self.heuristic_rules.append("no_ignored_input")
    
        if enable_rule_no_meaningless_command:
            self.heuristic_rules.append("no_meaningless_command")
        
        if enable_rule_no_sort_non_numeric_with_numeric_input:
            self.heuristic_rules.append("no_sort_non_numeric_with_numeric_input")

        if enable_rule_no_empty_output:
            self.heuristic_rules.append("no_empty_output")

        self.shell_parser = ShellParser(
            pipeline_address,
            enable_user_annotations,
            check_all_pipelines,
            enable_concretization=enable_concretization,
        )

    def initialize_check(self):
        self.pipelines = self.shell_parser.parse_pipeline()
        self.pipeline_nodes = self.shell_parser.pipeline_nodes
        self.annotations = self.shell_parser.annotations
        self.env_annotations = self.shell_parser.env_annotations
        self.current_index = 0
        
        for pipeline in self.pipeline_nodes:
            logging.debug(f"Pipeline: {pretty_ast_node(pipeline)}")

    def check_next(self) -> Optional[CheckingResult]:
        if not self.pipelines:
            self.initialize_check()
            assert self.pipelines is not None

        if self.pipeline_nodes is None:
            return None
            
        if self.current_index >= len(self.pipelines):
            return None
        
        if self.env_annotations.get(self.pipeline_nodes[self.current_index], {}).get("__input_pattern__", None) is not None:
            initial_output_type = self.env_annotations[self.pipeline_nodes[self.current_index]]["__input_pattern__"][0].pattern
        else:
            initial_output_type = ""

        parsed_commands = self.pipelines[self.current_index]
        pipeline_node = self.pipeline_nodes[self.current_index]

        # Increment the index before delegating the heavy logic to the
        # `PipelineChecker` so that the iterator semantics remain the same
        # from the caller's perspective.
        self.current_index += 1

        logging.info(f"Checking pipeline: {pretty_ast_node(pipeline_node)}")



        # Instantiate a fresh `PipelineChecker` with only the required
        # information instead of passing the whole `ScriptChecker` instance.
        pipeline_checker = PipelineChecker(
            annotations=self.annotations,
            env_annotations=self.env_annotations,
            heuristic_rules=self.heuristic_rules,
            enable_detailed_error_reporting=self.enable_detailed_error_reporting,
        )
        error_results = pipeline_checker.check(pipeline_node, parsed_commands, initial_output_type)
        # record["error_results"] = error_results
        # record["self_contained"] = pipeline_checker.self_contained
        return CheckingResult(
            error_results=error_results,
            self_contained=pipeline_checker.self_contained,
            pipeline_content=pretty_ast_node(pipeline_node),
            pipeline_length=pipeline_checker.pipeline_length,
            max_automata_size=pipeline_checker.max_automata_size,
            statistics_time=pipeline_checker.statistics_time,
            runtime_error_kind=pipeline_checker.runtime_error_kind,
            runtime_error_message=pipeline_checker.runtime_error_message,
            runtime_error_type=pipeline_checker.runtime_error_type,
            runtime_error_traceback=pipeline_checker.runtime_error_traceback,
        )

    def __iter__(self):
        self.initialize_check()
        return self
        
    def __next__(self) -> CheckingResult:
        result = self.check_next()
        if result is None:
            raise StopIteration
        return result

    def get_current_pipeline_content_when_error(self) -> Optional[str]:
        try:
            if self.pipeline_nodes is None:
                return None

            return self.pipeline_nodes[self.current_index - 1].pretty()
        except Exception:
            return None
        

class PipelineChecker:
    """Detailed type-checking logic for a single shell pipeline.

    The checker is instantiated on-demand from `ScriptChecker.check_next` and
    receives *only* the data it needs, avoiding a hard dependency on the whole
    `ScriptChecker` instance.
    """

    def __init__(
        self,
        annotations: Dict[CommandNode, List[UserAnnotation]],
        env_annotations: Dict[PipeNode, Dict[str, List[EnvAnnotation]]],
        heuristic_rules: List[str],
        enable_detailed_error_reporting: bool = True,
    ) -> None:
        self.annotations = annotations
        self.env_annotations = env_annotations
        self.heuristic_rules = heuristic_rules
        self.enable_detailed_error_reporting = enable_detailed_error_reporting
        # Track statistics for potential error reporting
        self.pipeline_length = 0
        self.max_automata_size = 1
        self.statistics_time = 0.0
        self.self_contained = True
        self.backward_map: Dict[int, Callable[[str], str] | None] = {}
        self.runtime_error_kind: Optional[str] = None
        self.runtime_error_message: Optional[str] = None
        self.runtime_error_type: Optional[str] = None
        self.runtime_error_traceback: Optional[str] = None

    # -------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------
    def check(self, pipeline_node: PipeNode, parsed_commands: List[Tuple[CommandSignature, CommandInvocationInitial]], initial_output_type: str) -> List[ErrorResult]:
        """Perform type checking on a single pipeline.

        Parameters
        ----------
        pipeline_node
            The AST node representing the pipeline.
        parsed_commands
            A list of tuples `(signature, invocation)` produced by the parser.
        initial_output_type
            The assumed input type for the first command in the pipeline
            (empty string means universal input).
        """
        previous_output_type = RegularType(initial_output_type)
        error_results: List[ErrorResult] = []

        # ---------------------------------------------------------
        # Logging record initialisation (same as original behaviour)
        # ---------------------------------------------------------
        self.pipeline_length = len(parsed_commands)

        # dummy command signature to ensure `signature` is not unbound in the `except` block
        signature = CommandSignature("fake command", "", "", [], [], [], True, True)
        
        try:
            # --------------------------------------------------
            # Iterate through each command in the pipeline
            # --------------------------------------------------
            pipeline_id = time.time_ns()
            for command_node, parsed_command, command_index in zip(pipeline_node.items, parsed_commands, range(len(parsed_commands))):
                signature, parsed_command_invocation = parsed_command

                assert isinstance(parsed_command_invocation, CommandInvocationInitial)
                corresponding_annotations = self.annotations.get(command_node, []) if isinstance(command_node, CommandNode) else []
                corresponding_env_annotations = self.env_annotations.get(pipeline_node, {})

                logging.debug(f"Annotations: {corresponding_annotations}")

                # ----------------------------------------------
                # Input type derivation
                # ----------------------------------------------
                input_type, no_input_type = signature.determine_input_type(
                    parsed_command_invocation,
                    corresponding_annotations,
                    self.heuristic_rules,
                    corresponding_env_annotations,
                )

                # ----------------------------------------------
                # Output type derivation
                # ----------------------------------------------
                inference_result = signature.determine_output_type(
                    previous_output_type,
                    parsed_command_invocation,
                    corresponding_annotations,
                    corresponding_env_annotations,
                )
                self_contained = True
                backward_func = None
                if isinstance(inference_result, InferenceResult):
                    backward_func = inference_result.backward_func
                    self_contained = inference_result.self_contained
                    current_output_type = inference_result.output_type
                else:
                    current_output_type = inference_result
                assert isinstance(current_output_type, RegularType)

                if self_contained is not None and not self_contained:
                    self.self_contained = False
                
                self.backward_map[command_index] = backward_func

                # ----------------------------------------------
                # Output automata post-processing & stats
                # ----------------------------------------------
                current_output_type.nfa.setDeterministic(False)
                current_output_type.nfa.determinize()
                current_output_type.nfa.removeDeadTransitions()
                current_output_type.nfa.minimize()

                statistics_start = time.perf_counter()
                current_automata_size = automata_size_for_statistics(current_output_type)
                self.statistics_time += time.perf_counter() - statistics_start
                self.max_automata_size = max(self.max_automata_size, current_automata_size)

                # ----------------------------------------------
                # Type constraint checks (domain constraints & heuristics)
                # ----------------------------------------------
                is_subtype, witness = previous_output_type.is_subtype(input_type)
                if not is_subtype:
                    intersection = previous_output_type & input_type
                    all_input = intersection.is_empty()
                    serious_violation = not input_type.is_empty() # if input type is empty, it is caught by a heuristic rule which is not serious violation
                    error_message = f"Input type '{previous_output_type}' is not compatible with expected input '{input_type}' for command '{signature.command_name}'. For example: '{witness}'."
                    
                    error_result = ErrorResult(
                        message=error_message,
                        witness=witness,
                        serious_violation=serious_violation,
                        all_input=all_input,
                        command_name=signature.command_name,
                        command_index=command_index + 1,
                    )
                    if self.enable_detailed_error_reporting:
                        error_result.all_input = previous_output_type.empty_intersection(input_type)
                    
                    error_results.append(error_result)
                    # Continue checking subsequent commands
                    previous_output_type = current_output_type
                    continue

                if no_input_type is not None and not (previous_output_type.is_empty() or previous_output_type.is_empty_string()):
                    is_not_subtype, witness = previous_output_type.not_subtype(no_input_type)
                    if not is_not_subtype:
                        error_message = f"Command '{signature.command_name}' received input '{previous_output_type}' but it should not accept input type which is subset of '{no_input_type}' according to heuristic rules."
                        
                        error_result = ErrorResult(
                            message=error_message,
                            all_input=True,
                            serious_violation=False,
                            command_name=signature.command_name,
                            command_index=command_index + 1,
                        )
                        
                        error_results.append(error_result)
                        previous_output_type = current_output_type
                        continue

                # ----------------------------------------------
                # Empty output rule
                # ----------------------------------------------
                if "no_empty_output" in self.heuristic_rules:
                    if current_output_type.is_empty() or current_output_type.is_empty_string():
                        error_message = f"Output type '{current_output_type}' is empty for command '{signature.command_name}'."
                        
                        error_result = ErrorResult(
                            message=error_message,
                            all_input=True,
                            serious_violation=False,
                            command_name=signature.command_name,
                            command_index=command_index + 2,
                        )
                        
                        error_results.append(error_result)
                        previous_output_type = current_output_type
                        continue

                # ----------------------------------------------
                # Assertions from user annotations
                # ----------------------------------------------
                for annotation in corresponding_annotations:
                    if annotation.annotation_type == AnnotationType.ASSERT:
                        # `@output "..."` is typically line-oriented unless the
                        # asserted regex itself explicitly mentions newlines.
                        asserted_output_type = RegularType(annotation.pattern)
                        stream_assertion = pattern_mentions_newline(annotation.pattern)
                        checked_output_type = current_output_type if stream_assertion else current_output_type.to_line_based_repr()
                        is_assertion_violated, witness = checked_output_type.is_subtype(asserted_output_type)
                        is_assertion_violated = not is_assertion_violated  # Negate because we want to check if assertion is violated
                        if is_assertion_violated:
                            intersection = checked_output_type & asserted_output_type
                            all_input = intersection.is_empty()
                                                        
                            error_message = f"Output type '{current_output_type}' is not compatible with asserted output '{annotation}' for command '{signature.command_name}'. For example: '{witness}'."

                            error_result = ErrorResult(
                                message=error_message,
                                witness=witness,
                                all_input=all_input,
                                serious_violation=True,
                                command_name=signature.command_name,
                                command_index=command_index + 2,
                            )
                            if self.enable_detailed_error_reporting:
                                error_result.all_input = checked_output_type.empty_intersection(asserted_output_type)
                            
                            error_results.append(error_result)
                            previous_output_type = current_output_type
                            continue

                for annotation in corresponding_annotations:
                    if annotation.annotation_type == AnnotationType.ASSERT_CONTAINS:
                        # `output_contains` is line-oriented: check membership against the
                        # line-based language even when the command currently carries a
                        # stream representation.
                        line_based_output_type = current_output_type.to_line_based_repr()
                        asserted_line_type = RegularType(annotation.pattern)
                        is_contains_violated, witness = asserted_line_type.is_subtype(line_based_output_type)
                        is_contains_violated = not is_contains_violated  # Negate because we want to check if assertion is violated
                        if is_contains_violated:
                            error_message = f"Output type '{current_output_type}' does not contain '{annotation}' for command '{signature.command_name}'. For example: '{witness}'."
                            
                            error_result = ErrorResult(
                                message=error_message,
                                witness=witness,
                                all_input=True,
                                serious_violation=True,
                                command_name=signature.command_name,
                                command_index=command_index + 2,
                            )
                            if self.enable_detailed_error_reporting:
                                error_result.all_input = line_based_output_type.empty_intersection(asserted_line_type)
                            
                            error_results.append(error_result)
                            previous_output_type = current_output_type
                            continue

                # ----------------------------------------------
                # Prepare for next iteration
                # ----------------------------------------------
                previous_output_type = current_output_type

                logging.debug("-" * 60)
                logging.debug(f"current command: {signature.command_name}")
                logging.debug(f"Output type: {current_output_type}")
                logging.debug("-" * 60)

        except ToolError as e:
            error_result = ErrorResult(
                message=str(e),
                tainted=True,
                command_name=signature.command_name,
                all_input=True,
                serious_violation=True,
            )
            # Tool errors terminate checking immediately.
            return error_results + [error_result]

        except PashAnnotationParsingError as e:
            self._capture_runtime_error("pash annotations error", e)
            return error_results

        except Exception as e:
            self._capture_runtime_error("tool runtime error", e)
            return error_results

        return error_results

    def _capture_runtime_error(self, kind: str, error: Exception) -> None:
        self.runtime_error_kind = kind
        self.runtime_error_message = str(error)
        self.runtime_error_type = type(error).__name__
        self.runtime_error_traceback = traceback.format_exc()
    

    def backward(self, witness: str, command_index: int) -> Tuple[str, int]:
        if not CONFIG["enable_FST"]:
            return witness, command_index
        real_command_index = command_index - 1 # offset by 1 because command_index is 1-indexed
        witness = re.escape(witness)
        witness_nfa = RegularType(witness).nfa
        current_nfa = witness_nfa
        while (real_command_index - 1) in self.backward_map:
            backward_func = self.backward_map[real_command_index - 1]
            if backward_func is None:
                break
            current_nfa = backward_func(current_nfa)
            if isinstance(current_nfa, str):
                current_nfa = RegularType(re.escape(current_nfa)).nfa
            real_command_index -= 1
        return str(current_nfa.getShortestExample(True)), real_command_index
