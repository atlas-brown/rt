import logging
from stream.regular_type import RegularType
from stream.parser.shell_parser import ShellParser
from typing import Optional
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from stream.checking_result import CheckingResult
from stream.tool_error import ToolError
from stream.user_annotation import AnnotationType
from stream.utils.logger import get_logger
from stream.utils.timing import Timing

class TypeChecker:
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
        ) -> None:
        self.pipelines = None
        self.pipeline_nodes = None
        self.current_index = 0
        self.enable_stage_timeout = enable_stage_timeout
        self.stage_timeout = stage_timeout
        self.enable_user_annotations = enable_user_annotations
        self.check_all_pipelines = check_all_pipelines
        
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

    def check_subtype(self, type1: RegularType, type2: RegularType) -> CheckingResult:
        return type1.is_subtype(type2)
    
    def check_not_subtype(self, type1: RegularType, type2: RegularType) -> CheckingResult:
        result = self.check_subtype(type1, type2)
        if result.ill_typed:
            return CheckingResult(False)
        return CheckingResult(True)

    def check_next(self) -> Optional[CheckingResult]:
        if not self.pipelines:
            self.initialize_check()

        if self.pipeline_nodes is None:
            return None
            
        if self.current_index >= len(self.pipelines):
            return None
        
        if self.env_annotations.get(self.pipeline_nodes[self.current_index], {}).get("__input_pattern__", None) is not None:
            previous_output_type = RegularType(self.env_annotations[self.pipeline_nodes[self.current_index]]["__input_pattern__"][0].pattern)
        else:
            previous_output_type = RegularType("") # start with empty string type by default

        parsed_commands = self.pipelines[self.current_index]
        pipeline_node = self.pipeline_nodes[self.current_index]

        record = get_logger().create_record()
        record["pipeline"] = pipeline_node.pretty().replace("\\\\", "\\")
        record["command_list"] = []
        record["RT_warning"] = False

        self.current_index += 1
        logging.info(f"Checking pipeline: {pipeline_node.pretty()}")
        checking_result = CheckingResult(False, pipeline_node)
        
        try:
            # Calculate pipeline length - number of commands in the pipeline
            checking_result.set_pipeline_length(len(parsed_commands))
            
            checking_result.set_max_automata_size(1)
            
            for command_node, parsed_command in zip(pipeline_node.items, parsed_commands):
                signature, parsed_command_invocation = parsed_command
                
                assert isinstance(parsed_command_invocation, CommandInvocationInitial)

                command_list = get_logger().get_latest_record()["command_list"]
                command_list.append({})
                command_list[-1]["command_name"] = parsed_command_invocation.cmd_name
                get_logger().add_command_log(parsed_command_invocation.cmd_name)

                corresponding_annotations = self.annotations.get(command_node, [])
                corresponding_env_annotations = self.env_annotations.get(pipeline_node, {})
                logging.debug(f"Annotations: {corresponding_annotations}")
                with Timing("timing input type creation = "):
                    input_type, no_input_type = signature.determine_input_type(parsed_command_invocation, corresponding_annotations, self.heuristic_rules, corresponding_env_annotations)

                    
                with Timing("timing output type creation = "):
                    current_output_type = signature.determine_output_type(previous_output_type, parsed_command_invocation, corresponding_annotations, corresponding_env_annotations)

                input_type_str = input_type.pattern
                no_input_type_str = no_input_type.pattern if no_input_type is not None else None
                current_output_type_str = get_logger().get_latest_record()["command_list"][-1]["output_type"]

                command_type_str = ""
                if "α" not in current_output_type_str and no_input_type_str is None:
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

                current_output_type.nfa.setDeterministic(False)
                current_output_type.nfa.removeDeadTransitions()
                current_output_type.nfa.minimize()
                
                # Update max automata size in the checking result
                current_automata_size = len(current_output_type.nfa.getStates())
                max_automata_size = max(checking_result.max_automata_size, current_automata_size)
                checking_result.set_max_automata_size(max_automata_size)

                get_logger().get_latest_record()["command_list"][-1]["output_size"] = current_automata_size
                

                checking_result.set(self.check_subtype(previous_output_type, input_type))
                if checking_result.ill_typed:
                    checking_result.set_message(
                        f"Input type '{previous_output_type}' is not compatible with expected input '{input_type}' for command '{signature.command_name}'. For example: '{checking_result.counterexample}'."
                    )
                    get_logger().get_latest_record()["RT_warning"] = True
                    get_logger().get_latest_record()["error_message"] = checking_result.message
                    get_logger().get_latest_record()["error_type"] = "type mismatch"
                    return checking_result
                
                if no_input_type is not None:
                    checking_result.set(self.check_not_subtype(previous_output_type, no_input_type))
                    if checking_result.ill_typed:
                        checking_result.set_message(
                            f"Command '{signature.command_name}' received input '{previous_output_type}' "
                            f"but it should not accept input type which is subset of '{no_input_type}' according to heuristic rules."
                        )
                        checking_result.tainted = no_input_type.tainted
                        get_logger().get_latest_record()["RT_warning"] = True
                        get_logger().get_latest_record()["error_message"] = checking_result.message
                        get_logger().get_latest_record()["error_type"] = "type mismatch"
                        return checking_result

                # check if the output is empty
                if self.enable_rule_no_empty_output:
                    if current_output_type.is_empty() or current_output_type.is_empty_string():
                        checking_result.set_ill_typed(True)
                        checking_result.set_message(
                            f"Output type '{current_output_type}' is empty for command '{signature.command_name}'."
                        )
                        checking_result.tainted = False
                        get_logger().get_latest_record()["RT_warning"] = True
                        get_logger().get_latest_record()["error_message"] = checking_result.message
                        get_logger().get_latest_record()["error_type"] = "empty output"
                        return checking_result

                # process assert annotation
                for annotation in corresponding_annotations:
                    if annotation.annotation_type == AnnotationType.ASSERT:
                        checking_result.set(self.check_subtype(current_output_type, RegularType(annotation.pattern)))
                        if checking_result.ill_typed:
                            checking_result.set_message(
                                f"Output type '{current_output_type}' is not compatible with asserted output '{annotation}' for command '{signature.command_name}'. For example: '{checking_result.counterexample}'."
                            )
                            if "\n" not in annotation.pattern:
                                checking_result.tainted = current_output_type.tainted
                            else:
                                checking_result.tainted = True
                            get_logger().get_latest_record()["RT_warning"] = True
                            get_logger().get_latest_record()["error_message"] = checking_result.message.replace(" For example: 'None'.", "")
                            get_logger().get_latest_record()["error_type"] = "assertion failed"
                            get_logger().get_latest_record()["command_list"][-1]["output_asserted"] = annotation.pattern
                            return checking_result
                        
                for annotation in corresponding_annotations:
                    if annotation.annotation_type == AnnotationType.ASSERT_CONTAINS:
                        checking_result.set(self.check_subtype(RegularType(annotation.pattern), current_output_type))
                        if checking_result.ill_typed:
                            checking_result.set_message(
                                f"Output type '{current_output_type}' does not contain '{annotation}' for command '{signature.command_name}'. For example: '{checking_result.counterexample}'."
                            )
                            checking_result.tainted = False
                            get_logger().get_latest_record()["RT_warning"] = True
                            get_logger().get_latest_record()["error_message"] = checking_result.message
                            get_logger().get_latest_record()["error_type"] = "assertion failed"
                            get_logger().get_latest_record()["command_list"][-1]["output_asserted"] = annotation.pattern
                            return checking_result

                previous_output_type = current_output_type

                logging.debug("-"*60)
                logging.debug(f"current command: {signature.command_name}")
                logging.debug(f"Output type: {current_output_type}")
                logging.debug("-"*60)

        except ToolError as e:
            checking_result.set_ill_typed(True)
            checking_result.set_message(str(e))
            get_logger().get_latest_record()["error_message"] = str(e)
            get_logger().get_latest_record()["RT_warning"] = True
            get_logger().get_latest_record()["error_type"] = "tool error"
            return checking_result
        
        except Exception as e:
            checking_result.set_ill_typed(False)
            checking_result.set_message(str(e))
            get_logger().remove_latest_record()
            return checking_result
        
        return checking_result


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
