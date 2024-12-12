import logging
from stream.regular_type import RegularType
from stream.shell_parser import ShellParser
from typing import Optional
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from stream.checking_result import CheckingResult
from stream.tool_error import ToolError
from stream.user_annotation import AnnotationType

class TypeChecker:
    def __init__(self, 
                 pipeline_address: str, 
                 enable_user_annotations: bool = True,
                 enable_rule_empty_output: bool = True,
                 enable_rule_no_ignored_input: bool = True,
                 enable_stage_timeout: bool = False,
                 stage_timeout: int = 10
        ) -> None:
        self.pipelines = None
        self.pipeline_nodes = None
        self.current_index = 0
        self.enable_stage_timeout = enable_stage_timeout
        self.stage_timeout = stage_timeout
        self.enable_user_annotations = enable_user_annotations
        self.enable_rule_empty_output = enable_rule_empty_output
        self.enable_rule_no_ignored_input = enable_rule_no_ignored_input
        self.shell_parser = ShellParser(pipeline_address, enable_user_annotations)

    def initialize_check(self):
        self.pipelines = self.shell_parser.parse_pipeline()
        self.pipeline_nodes = self.shell_parser.pipeline_nodes
        self.annotations = self.shell_parser.annotations
        self.current_index = 0
        
        for pipeline in self.pipeline_nodes:
            logging.debug(f"Pipeline: {pipeline.pretty()}")

    def check_subtype(self, type1: RegularType, type2: RegularType) -> CheckingResult:
        if self.enable_stage_timeout:
            return type1.is_subtype_with_timeout(type2, self.stage_timeout)
        return type1.is_subtype(type2)

    def check_next(self) -> Optional[CheckingResult]:
        if not self.pipelines:
            self.initialize_check()

        if self.pipeline_nodes is None:
            return None
            
        if self.current_index >= len(self.pipelines):
            return None
        
        previous_output_type = RegularType("") # start with empty string type
        parsed_commands = self.pipelines[self.current_index]
        pipeline_node = self.pipeline_nodes[self.current_index]
        self.current_index += 1
        logging.info(f"Checking pipeline: {pipeline_node.pretty()}")
        checking_result = CheckingResult(False, pipeline_node)
        
        try:
            for command_node, parsed_command in zip(pipeline_node.items, parsed_commands):
                signature, parsed_command_invocation = parsed_command
                
                assert isinstance(parsed_command_invocation, CommandInvocationInitial)
                
                # process the rule that the input cannot be ignored
                if self.enable_rule_no_ignored_input and signature.ignore_input and not previous_output_type.is_empty() and not previous_output_type.is_empty_string():
                    checking_result.set_ill_typed(True)
                    checking_result.set_message(
                        f"Input type '{previous_output_type.pattern}' is ignored for command '{signature.command_name}'."
                    )
                    return checking_result


                corresponding_annotations = self.annotations.get(command_node, [])
                input_type = signature.determine_input_type(parsed_command_invocation, corresponding_annotations)
                
                checking_result.set(self.check_subtype(previous_output_type, input_type))
                
                if checking_result.ill_typed:
                    checking_result.set_message(
                        f"Input type '{previous_output_type.pattern}' is not compatible with expected input '{input_type.pattern}' for command '{signature.command_name}'."
                    )
                    return checking_result
                    
                current_output_type = signature.determine_output_type(previous_output_type, parsed_command_invocation, corresponding_annotations)

                # check if the output is empty
                if self.enable_rule_empty_output:
                    if current_output_type.is_empty() or current_output_type.is_empty_string():
                        checking_result.set_ill_typed(True)
                        checking_result.set_message(
                            f"Output type '{current_output_type.pattern}' is empty for command '{signature.command_name}'."
                        )
                        return checking_result

                # process assert annotation
                for annotation in corresponding_annotations:
                    if annotation.annotation_type == AnnotationType.ASSERT:
                        checking_result.set(self.check_subtype(current_output_type, RegularType(annotation.pattern)))
                        if checking_result.ill_typed:
                            checking_result.set_message(
                                f"Output type '{previous_output_type.pattern}' is not compatible with asserted output '{annotation.pattern}' for command '{signature.command_name}'."
                            )
                            return checking_result

                previous_output_type = current_output_type

        except ToolError as e:
            checking_result.set_ill_typed(True)
            checking_result.set_message(str(e))
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
