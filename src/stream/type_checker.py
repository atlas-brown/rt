import logging
import re
import traceback
import copy
from dataclasses import dataclass
from stream.command_signature import CommandSignature, InferenceResult
from stream.regular_type import RegularType
from stream.parser.shell_parser import ShellParser
from typing import Callable, Dict, Optional, List, Tuple
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from stream.tool_error import ToolError
from stream.user_annotation import AnnotationType, UserAnnotation
from stream.utils.logger import get_logger
from stream.utils.format import pretty_ast_node
from stream.utils.timing import Timing
from shasta.ast_node import PipeNode

@dataclass
class ErrorResult:
    """Represents a type checking error found during pipeline analysis.
    
    Each instance represents a discovered error. All fields have default values.
    """
    # pipe_node = None
    message: Optional[str] = None
    witness: Optional[str] = None
    derivation_trace: Optional[List[str]] = None
    all_input: Optional[bool]= None
    serious_violation: Optional[bool] = None
    # pipeline_content: Optional[str] = None
    # pipeline_length: int = 0
    # max_automata_size: int = 1
    tainted: Optional[bool] = None


#
# self_contained (ground truth): True
# errors(ground): [{
     # serious_violation: True
     # all_input: True
# }]
# self_contained (compute): True
# errors(compute): [{
     # serious_violation: True
     # all_input: True
# }]


@dataclass
class CheckingResult:
    error_results: List[ErrorResult]
    self_contained: bool
    pipeline_content: str
    pipeline_length: int
    max_automata_size: int


class ScriptChecker:
    def __init__(self, 
                 pipeline_address: str, 
                 enable_user_annotations: bool = True,
                 enable_rule_no_empty_output: bool = True,
                 enable_rule_no_ignored_input: bool = True,
                #  enable_rule_no_space_in_file_name = True,
                 enable_rule_no_meaningless_command = True,
                 enable_rule_no_sort_non_numeric_with_numeric_input = True,
                 enable_stage_timeout: bool = False,
                 stage_timeout: int = 10,
                 check_all_pipelines: bool = True,
                 label: bool = True,
                 enable_detailed_error_reporting: bool = True
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

        # if enable_rule_no_space_in_file_name:
        self.heuristic_rules.append("no_space_in_file_name")

        if enable_rule_no_ignored_input:
            self.heuristic_rules.append("no_ignored_input")
    
        if enable_rule_no_meaningless_command:
            self.heuristic_rules.append("no_meaningless_command")
        
        if enable_rule_no_sort_non_numeric_with_numeric_input:
            self.heuristic_rules.append("no_sort_non_numeric_with_numeric_input")

        if enable_rule_no_empty_output:
            self.heuristic_rules.append("no_empty_output")

        self.shell_parser = ShellParser(pipeline_address, enable_user_annotations, check_all_pipelines)

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

        record = get_logger().create_record()
        record["script_address"] = self.pipeline_address
        record["buggy (ground truth)"] = not self.label
        record["pipeline"] = pretty_ast_node(pipeline_node)
        record["command_list"] = []
        record["error_results"] = []
        record["RT_warning"] = False

        logging.info(f"Checking pipeline: {pretty_ast_node(pipeline_node)}")



        # Instantiate a fresh `PipelineChecker` with only the required
        # information instead of passing the whole `ScriptChecker` instance.
        pipeline_checker = PipelineChecker(
            annotations=self.annotations,
            env_annotations=self.env_annotations,
            heuristic_rules=self.heuristic_rules,
            enable_detailed_error_reporting=self.enable_detailed_error_reporting,
        )
        return CheckingResult(
            error_results=pipeline_checker.check(pipeline_node, parsed_commands, initial_output_type),
            self_contained=pipeline_checker.self_contained,
            pipeline_content=pretty_ast_node(pipeline_node),
            pipeline_length=pipeline_checker.pipeline_length,
            max_automata_size=pipeline_checker.max_automata_size
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
        annotations: Dict[PipeNode, List[UserAnnotation]],
        env_annotations: Dict[PipeNode, Dict[str, List[UserAnnotation]]],
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
        self.self_contained = True
        self.backward_map: Dict[PipeNode, Callable[[str], str] | None] = {}

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
        try:

            # --------------------------------------------------
            # Iterate through each command in the pipeline
            # --------------------------------------------------
            for command_node, parsed_command in zip(pipeline_node.items, parsed_commands):
                signature, parsed_command_invocation = parsed_command

                assert isinstance(parsed_command_invocation, CommandInvocationInitial)

                command_list = get_logger().get_latest_record()["command_list"]
                command_list.append({})
                command_list[-1]["command_name"] = pretty_ast_node(command_node)
                get_logger().add_command_log(parsed_command_invocation.cmd_name)
                if parsed_command_invocation.cmd_name in ["grep", "cut", "awk", "sed", "tr", "paste", "fmt"]:
                    # Extract flags and operands for detailed logging
                    flags = [flag.get_name() for flag in parsed_command_invocation.flag_option_list]
                    operands = [op.name for op in parsed_command_invocation.operand_list]
                    full_invocation = pretty_ast_node(command_node)
                    
                    # Record the detailed command invocation
                    get_logger().add_detailed_command_invocation(
                        command_name=parsed_command_invocation.cmd_name,
                        invocation=full_invocation,
                        flags=flags,
                        operands=operands
                    )
                    
                    # Record pattern analysis for grep and sed commands
                    if parsed_command_invocation.cmd_name in ["grep", "sed"]:
                        get_logger().add_pattern_analysis(
                            command_name=parsed_command_invocation.cmd_name,
                            invocation=pretty_ast_node(command_node),
                            pattern="",  # Will be updated in special signatures
                            ast_repr="",  # Will be updated in special signatures
                            is_pure_string=False,  # Will be updated in special signatures
                            has_references=False  # Will be updated in special signatures
                        )
                corresponding_annotations = self.annotations.get(command_node, [])
                corresponding_env_annotations = self.env_annotations.get(pipeline_node, {})
                if len(corresponding_annotations) > 0:
                    get_logger().get_latest_record()["annotations"] = corresponding_annotations
                if len(corresponding_env_annotations) > 0:
                    get_logger().get_latest_record()["env_annotations"] = corresponding_env_annotations

                logging.debug(f"Annotations: {corresponding_annotations}")

                # ----------------------------------------------
                # Input type derivation
                # ----------------------------------------------
                with Timing("timing input type creation = "):
                    input_type, no_input_type = signature.determine_input_type(
                        parsed_command_invocation,
                        corresponding_annotations,
                        self.heuristic_rules,
                        corresponding_env_annotations,
                    )

                # ----------------------------------------------
                # Output type derivation
                # ----------------------------------------------
                with Timing("timing output type creation = "):
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
                    
                    self.backward_map[pipeline_node] = backward_func

                # ----------------------------------------------
                # Pretty printing of type information for logging
                # ----------------------------------------------
                input_type_str = input_type.pattern
                no_input_type_str = no_input_type.pattern if no_input_type is not None else None
                current_output_type_str = get_logger().get_latest_record()["command_list"][-1]["output_type"]
                current_output_type_str = refine_log(current_output_type_str)

                command_type_str = ""
                input_type_str = refine_log(input_type_str)
                current_output_type_str = refine_log(current_output_type_str)
                if "α" not in current_output_type_str and no_input_type_str is None:
                    if input_type_str == "":
                        input_type_str = "()"
                    command_type_str = f"{input_type_str} -> {current_output_type_str}"
                elif no_input_type_str is None and input_type_str == ".*":
                    command_type_str = f"∀ α . α -> {current_output_type_str}"
                elif no_input_type_str is None and input_type_str != ".*":
                    command_type_str = f"∀ α ⊆ {input_type_str} . α -> {current_output_type_str}"
                elif no_input_type_str is not None and input_type_str == ".*":
                    command_type_str = f"∀ α ⊄ {no_input_type_str} . α -> {current_output_type_str}"
                elif no_input_type_str is not None and input_type_str != ".*":
                    command_type_str = f"∀ α ⊆ {input_type_str} ∧ α ⊄ {no_input_type_str}. α -> {current_output_type_str}"

                get_logger().get_latest_record()["command_list"][-1]["command_type"] = command_type_str
                get_logger().get_latest_record()["command_list"][-1].pop("output_type")

                # ----------------------------------------------
                # Output automata post-processing & stats
                # ----------------------------------------------
                current_output_type.nfa.setDeterministic(False)
                current_output_type.nfa.removeDeadTransitions()
                current_output_type.nfa.minimize()

                current_automata_size = len(current_output_type.nfa.getStates())
                self.max_automata_size = max(self.max_automata_size, current_automata_size)

                cmd_log_entry = get_logger().get_latest_record()["command_list"][-1]
                cmd_log_entry["output_language_size"] = current_automata_size
                if current_output_type.get_singleton() is not None:
                    cmd_log_entry["output_language"] = current_output_type.get_singleton()
                elif current_automata_size <= 4:
                    cmd_log_entry["output_language"] = current_output_type.to_regex()
                elif len(get_logger().get_latest_record()["command_list"]) > 1:
                    cmd_log_entry["output_language"] = current_output_type_str.replace(
                        "α", get_logger().get_latest_record()["command_list"][-2]["output_language"]
                    )
                else:
                    cmd_log_entry["output_language"] = current_output_type_str.replace("α", initial_output_type)

                cmd_log_entry["output_language"] = refine_log(cmd_log_entry["output_language"])

                # ----------------------------------------------
                # Type constraint checks (domain constraints & heuristics)
                # ----------------------------------------------
                is_subtype, witness = previous_output_type.is_subtype(input_type)
                if not is_subtype:
                    previous_output_type_str = get_logger().get_latest_record()["command_list"][-2]["output_language"] if len(get_logger().get_latest_record()["command_list"]) > 1 else ""
                    error_message = f"Input type '{previous_output_type_str}' is not compatible with expected input '{input_type}' for command '{signature.command_name}'. For example: '{witness}'."
                    
                    error_result = ErrorResult(
                        # pipe_node=pipeline_node,
                        message=error_message,
                        witness=witness,
                        # pipeline_length=pipeline_length,
                        # max_automata_size=max_automata_size,
                        # tainted=True,
                        serious_violation=True,
                    )
                    if self.enable_detailed_error_reporting:
                        error_result.all_input = previous_output_type.empty_intersection(input_type)
                    
                    get_logger().get_latest_record()["RT_warning"] = True
                    get_logger().get_latest_record()["error_message"] = error_message
                    get_logger().get_latest_record()["error_type"] = "type mismatch (domain constraint)"
                    error_results.append(error_result)
                    # Continue checking subsequent commands
                    previous_output_type = current_output_type
                    continue

                if no_input_type is not None:
                    is_not_subtype, witness = previous_output_type.not_subtype(no_input_type)
                    if not is_not_subtype:
                        previous_output_type_str = get_logger().get_latest_record()["command_list"][-2]["output_language"] if len(get_logger().get_latest_record()["command_list"]) > 1 else ""
                        error_message = f"Command '{signature.command_name}' received input '{previous_output_type_str}' but it should not accept input type which is subset of '{no_input_type}' according to heuristic rules."
                        
                        error_result = ErrorResult(
                            # pipe_node=pipeline_node,
                            message=error_message,
                            # witness=witness,
                            # pipeline_length=pipeline_length,
                            # max_automata_size=max_automata_size,
                            # tainted=no_input_type.tainted,
                            all_input=True,
                            serious_violation=False,
                        )
                        
                        get_logger().get_latest_record()["RT_warning"] = True
                        # get_logger().get_latest_record()["error_message"] = error_message
                        # get_logger().get_latest_record()["error_type"] = "heuristic rule violation"
                        get_logger().get_latest_record()["error_results"].append(error_result)
                        error_results.append(error_result)
                        previous_output_type = current_output_type
                        continue

                # ----------------------------------------------
                # Empty output rule
                # ----------------------------------------------
                if "no_empty_output" in self.heuristic_rules:
                    if current_output_type.is_empty() or current_output_type.is_empty_string():
                        current_output_type_str = cmd_log_entry['output_language']
                        error_message = f"Output type '{current_output_type_str}' is empty for command '{signature.command_name}'."
                        
                        error_result = ErrorResult(
                            # pipe_node=pipeline_node,
                            message=error_message,
                            # pipeline_length=pipeline_length,
                            # max_automata_size=max_automata_size,
                            # tainted=False,
                            all_input=True,
                            serious_violation=False,
                        )
                        
                        get_logger().get_latest_record()["RT_warning"] = True
                        # get_logger().get_latest_record()["error_message"] = error_message
                        # get_logger().get_latest_record()["error_type"] = "heuristic rule violation"
                        get_logger().get_latest_record()["error_results"].append(error_result)
                        error_results.append(error_result)
                        previous_output_type = current_output_type
                        continue

                # ----------------------------------------------
                # Assertions from user annotations
                # ----------------------------------------------
                for annotation in corresponding_annotations:
                    if annotation.annotation_type == AnnotationType.ASSERT:
                        is_assertion_violated, witness = current_output_type.is_subtype(RegularType(annotation.pattern))
                        is_assertion_violated = not is_assertion_violated  # Negate because we want to check if assertion is violated
                        if is_assertion_violated:
                            current_output_type_str = cmd_log_entry['output_language']
                            error_message = f"Output type '{current_output_type_str}' is not compatible with asserted output '{annotation}' for command '{signature.command_name}'. For example: '{witness}'."
                            
                            tainted = True if "\n" in annotation.pattern else current_output_type.tainted
                            
                            error_result = ErrorResult(
                                # pipe_node=pipeline_node,
                                message=error_message,
                                witness=witness,
                                # pipeline_length=pipeline_length,
                                # max_automata_size=max_automata_size,
                                # tainted=tainted,
                                serious_violation=True,
                            )
                            if self.enable_detailed_error_reporting:
                                error_result.all_input = current_output_type.empty_intersection(RegularType(annotation.pattern))
                            
                            get_logger().get_latest_record()["RT_warning"] = True
                            # get_logger().get_latest_record()["error_message"] = error_message
                            # get_logger().get_latest_record()["error_type"] = "type mismatch (assertion)"
                            get_logger().get_latest_record()["error_results"].append(error_result)
                            cmd_log_entry["output_asserted"] = annotation.pattern
                            error_results.append(error_result)
                            previous_output_type = current_output_type
                            continue

                for annotation in corresponding_annotations:
                    if annotation.annotation_type == AnnotationType.ASSERT_CONTAINS:
                        is_contains_violated, witness = RegularType(annotation.pattern).is_subtype(current_output_type)
                        is_contains_violated = not is_contains_violated  # Negate because we want to check if assertion is violated
                        if is_contains_violated:
                            current_output_type_str = cmd_log_entry['output_language']
                            error_message = f"Output type '{current_output_type_str}' does not contain '{annotation}' for command '{signature.command_name}'. For example: '{witness}'."
                            
                            error_result = ErrorResult(
                                # pipe_node=pipeline_node,
                                message=error_message,
                                witness=witness,
                                # pipeline_length=pipeline_length,
                                # max_automata_size=max_automata_size,
                                # tainted=False,
                                serious_violation=True,
                            )
                            if self.enable_detailed_error_reporting:
                                error_result.all_input = current_output_type.empty_intersection(RegularType(annotation.pattern))
                            
                            get_logger().get_latest_record()["RT_warning"] = True
                            # get_logger().get_latest_record()["error_message"] = error_message
                            # get_logger().get_latest_record()["error_type"] = "type mismatch (assertion)"
                            get_logger().get_latest_record()["error_results"].append(error_result)
                            cmd_log_entry["output_asserted"] = annotation.pattern
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
                # pipe_node=pipeline_node,
                message=str(e),
                # pipeline_length=pipeline_length,
                # max_automata_size=max_automata_size,
                tainted=True
            )
            get_logger().get_latest_record()["error_message"] = str(e)
            get_logger().get_latest_record()["RT_warning"] = True
            get_logger().get_latest_record()["error_type"] = "tool error"
            # Tool errors terminate checking immediately.
            return error_results + [error_result]

        except Exception as e:
            traceback.print_exc()
            # exit()
            # FIXME: This is a hack to handle tool errors.
            error_result = ErrorResult(
                # pipe_node=pipeline_node,
                message=str(e),
                # pipeline_length=pipeline_length,
                # max_automata_size=max_automata_size,
                tainted=True
            )
            get_logger().remove_latest_record()
            return []

        return error_results
    

    def backward(self, witness: str) -> str:
        pass

def refine_log(s: str) -> str:
    s = re.sub(r"((?<!\\)(?:\\\\)*)\\ ", r"\1 ", s)
    s = s.replace("\t", "\\t")
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    s = s.replace("\0", "\\0")
    if s.startswith(" "):
        s = "( )" + s[1:]
    return s
