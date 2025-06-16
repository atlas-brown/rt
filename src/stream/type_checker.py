import logging
import re
import traceback
import copy
from stream.regular_type import RegularType
from stream.parser.shell_parser import ShellParser
from typing import Optional, List
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from stream.checking_result import CheckingResult
from stream.tool_error import ToolError
from stream.user_annotation import AnnotationType
from stream.utils.logger import get_logger
from stream.utils.timing import Timing

class ScriptChecker:
    def __init__(self, 
                 pipeline_address: str, 
                 enable_user_annotations: bool = True,
                 enable_rule_no_empty_output: bool = True,
                 enable_rule_no_ignored_input: bool = True,
                 enable_rule_no_space_in_file_name = True,
                 enable_rule_no_meaningless_command = True,
                 enable_rule_no_sort_non_numeric_with_numeric_input = True,
                 enable_stage_timeout: bool = False,
                 stage_timeout: int = 10,
                 check_all_pipelines: bool = True,
                 label: bool = True
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
        self.heuristic_rules = []
        self.enable_rule_no_empty_output = enable_rule_no_empty_output
        if enable_rule_no_ignored_input:
            self.heuristic_rules.append("no_ignored_input")
        
        if enable_rule_no_space_in_file_name:
            self.heuristic_rules.append("no_space_in_file_name")

        if enable_rule_no_meaningless_command:
            self.heuristic_rules.append("no_meaningless_command")
        
        if enable_rule_no_sort_non_numeric_with_numeric_input:
            self.heuristic_rules.append("no_sort_non_numeric_with_numeric_input")

        self.shell_parser = ShellParser(pipeline_address, enable_user_annotations, check_all_pipelines)

    def initialize_check(self):
        self.pipelines = self.shell_parser.parse_pipeline()
        self.pipeline_nodes = self.shell_parser.pipeline_nodes
        self.annotations = self.shell_parser.annotations
        self.env_annotations = self.shell_parser.env_annotations
        self.current_index = 0
        
        for pipeline in self.pipeline_nodes:
            logging.debug(f"Pipeline: {pipeline.pretty()}")

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

        # Instantiate a fresh `PipelineChecker` with only the required
        # information instead of passing the whole `ScriptChecker` instance.
        pipeline_checker = PipelineChecker(
            annotations=self.annotations,
            env_annotations=self.env_annotations,
            heuristic_rules=self.heuristic_rules,
            label=self.label,
            pipeline_address=self.pipeline_address,
            enable_rule_no_empty_output=self.enable_rule_no_empty_output,
        )
        return pipeline_checker.check(pipeline_node, parsed_commands, initial_output_type)

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
        *,
        annotations,
        env_annotations,
        heuristic_rules,
        label: bool,
        pipeline_address: str,
        enable_rule_no_empty_output: bool,
    ) -> None:
        self.annotations = annotations
        self.env_annotations = env_annotations
        self.heuristic_rules = heuristic_rules
        self.label = label
        self.pipeline_address = pipeline_address
        self.enable_rule_no_empty_output = enable_rule_no_empty_output

    # -------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------
    def check(self, pipeline_node, parsed_commands, initial_output_type: str) -> CheckingResult:  # type: ignore[override]
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
        error_results: List[CheckingResult] = []

        # ---------------------------------------------------------
        # Logging record initialisation (same as original behaviour)
        # ---------------------------------------------------------
        record = get_logger().create_record()
        record["script_address"] = self.pipeline_address
        record["buggy (ground truth)"] = not self.label
        record["pipeline"] = pipeline_node.pretty().replace("\\\\", "\\")
        record["command_list"] = []
        record["RT_warning"] = False

        logging.info(f"Checking pipeline: {pipeline_node.pretty()}")
        checking_result = CheckingResult(False, pipeline_node)

        try:
            # --------------------------------------------------
            # Overall statistics setup
            # --------------------------------------------------
            checking_result.set_pipeline_length(len(parsed_commands))
            checking_result.set_max_automata_size(1)

            # --------------------------------------------------
            # Iterate through each command in the pipeline
            # --------------------------------------------------
            for command_node, parsed_command in zip(pipeline_node.items, parsed_commands):
                signature, parsed_command_invocation = parsed_command

                assert isinstance(parsed_command_invocation, CommandInvocationInitial)

                command_list = get_logger().get_latest_record()["command_list"]
                command_list.append({})
                command_list[-1]["command_name"] = parsed_command_invocation.cmd_name
                get_logger().add_command_log(parsed_command_invocation.cmd_name)

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
                    current_output_type = signature.determine_output_type(
                        previous_output_type,
                        parsed_command_invocation,
                        corresponding_annotations,
                        corresponding_env_annotations,
                    )

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
                max_automata_size = max(checking_result.max_automata_size, current_automata_size)
                checking_result.set_max_automata_size(max_automata_size)

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
                checking_result.set(previous_output_type.is_subtype(input_type))
                if checking_result.ill_typed:
                    previous_output_type_str = get_logger().get_latest_record()["command_list"][-2]["output_language"] if len(get_logger().get_latest_record()["command_list"]) > 1 else ""
                    checking_result.set_message(
                        f"Input type '{previous_output_type_str}' is not compatible with expected input '{input_type}' for command '{signature.command_name}'. For example: '{checking_result.counterexample}'."
                    )
                    get_logger().get_latest_record()["RT_warning"] = True
                    get_logger().get_latest_record()["error_message"] = checking_result.message
                    get_logger().get_latest_record()["error_type"] = "type mismatch (domain constraint)"
                    error_results.append(copy.deepcopy(checking_result))
                    # Continue checking subsequent commands
                    previous_output_type = current_output_type
                    continue

                if no_input_type is not None:
                    checking_result.set(previous_output_type.not_subtype(no_input_type))
                    if checking_result.ill_typed:
                        previous_output_type_str = get_logger().get_latest_record()["command_list"][-2]["output_language"] if len(get_logger().get_latest_record()["command_list"]) > 1 else ""
                        checking_result.set_message(
                            f"Command '{signature.command_name}' received input '{previous_output_type_str}' but it should not accept input type which is subset of '{no_input_type}' according to heuristic rules."
                        )
                        checking_result.tainted = no_input_type.tainted
                        get_logger().get_latest_record()["RT_warning"] = True
                        get_logger().get_latest_record()["error_message"] = checking_result.message
                        get_logger().get_latest_record()["error_type"] = "heuristic rule violation"
                        error_results.append(copy.deepcopy(checking_result))
                        previous_output_type = current_output_type
                        continue

                # ----------------------------------------------
                # Empty output rule
                # ----------------------------------------------
                if self.enable_rule_no_empty_output:
                    if current_output_type.is_empty() or current_output_type.is_empty_string():
                        checking_result.set_ill_typed(True)
                        current_output_type_str = cmd_log_entry['output_language']
                        checking_result.set_message(
                            f"Output type '{current_output_type_str}' is empty for command '{signature.command_name}'."
                        )
                        checking_result.tainted = False
                        get_logger().get_latest_record()["RT_warning"] = True
                        get_logger().get_latest_record()["error_message"] = checking_result.message
                        get_logger().get_latest_record()["error_type"] = "heuristic rule violation"
                        error_results.append(copy.deepcopy(checking_result))
                        previous_output_type = current_output_type
                        continue

                # ----------------------------------------------
                # Assertions from user annotations
                # ----------------------------------------------
                for annotation in corresponding_annotations:
                    if annotation.annotation_type == AnnotationType.ASSERT:
                        checking_result.set(current_output_type.is_subtype(RegularType(annotation.pattern)))
                        if checking_result.ill_typed:
                            current_output_type_str = cmd_log_entry['output_language']
                            checking_result.set_message(
                                f"Output type '{current_output_type_str}' is not compatible with asserted output '{annotation}' for command '{signature.command_name}'. For example: '{checking_result.counterexample}'."
                            )
                            if "\n" not in annotation.pattern:
                                checking_result.tainted = current_output_type.tainted
                            else:
                                checking_result.tainted = True
                            get_logger().get_latest_record()["RT_warning"] = True
                            get_logger().get_latest_record()["error_message"] = checking_result.message.replace(" For example: 'None'.", "")
                            get_logger().get_latest_record()["error_type"] = "type mismatch (assertion)"
                            cmd_log_entry["output_asserted"] = annotation.pattern
                            error_results.append(copy.deepcopy(checking_result))
                            previous_output_type = current_output_type
                            continue

                for annotation in corresponding_annotations:
                    if annotation.annotation_type == AnnotationType.ASSERT_CONTAINS:
                        checking_result.set(RegularType(annotation.pattern).is_subtype(current_output_type))
                        if checking_result.ill_typed:
                            current_output_type_str = cmd_log_entry['output_language']
                            checking_result.set_message(
                                f"Output type '{current_output_type_str}' does not contain '{annotation}' for command '{signature.command_name}'. For example: '{checking_result.counterexample}'."
                            )
                            checking_result.tainted = False
                            get_logger().get_latest_record()["RT_warning"] = True
                            get_logger().get_latest_record()["error_message"] = checking_result.message
                            get_logger().get_latest_record()["error_type"] = "type mismatch (assertion)"
                            cmd_log_entry["output_asserted"] = annotation.pattern
                            error_results.append(copy.deepcopy(checking_result))
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
            checking_result.set_ill_typed(True)
            checking_result.set_message(str(e))
            get_logger().get_latest_record()["error_message"] = str(e)
            get_logger().get_latest_record()["RT_warning"] = True
            get_logger().get_latest_record()["error_type"] = "tool error"
            # Tool errors terminate checking immediately.
            return checking_result

        except Exception as e:
            # Maintain previous behaviour – capture the exception as an error.
            checking_result.set_ill_typed(False)
            checking_result.set_message(str(e))
            get_logger().remove_latest_record()
            return checking_result

        return error_results[-1] if error_results else checking_result

def refine_log(s: str) -> str:
    s = re.sub(r"((?<!\\)(?:\\\\)*)\\ ", r"\1 ", s)
    s = s.replace("\t", "\\t")
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    s = s.replace("\0", "\\0")
    if s.startswith(" "):
        s = "( )" + s[1:]
    return s
