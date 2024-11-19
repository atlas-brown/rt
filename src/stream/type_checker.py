from stream.regular_type import RegularType
from stream.pipeline_parser import PipelineParser
from typing import Optional
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from stream.checking_result import CheckingResult

class TypeChecker:
    def __init__(self, pipeline_address: str) -> None:
        self.pipeline_parser = PipelineParser(pipeline_address)
        self.pipelines = None
        self.pipeline_nodes = None
        self.current_index = 0

    def initialize_check(self):
        self.pipelines = self.pipeline_parser.parse_pipeline()
        self.pipeline_nodes = self.pipeline_parser.pipeline_nodes
        self.current_index = 0

    def check_next(self) -> Optional[CheckingResult]:
        if not self.pipelines:
            self.initialize_check()
            
        if self.current_index >= len(self.pipelines):
            return None
        
        previous_output_type = RegularType("") # start with empty string type
        parsed_commands = self.pipelines[self.current_index]
        pipeline_node = self.pipeline_nodes[self.current_index]
        self.current_index += 1
        
        checking_result = CheckingResult(True, pipeline_node)
        
        for parsed_command in parsed_commands:
            signature, parsed_command_node = parsed_command
            
            assert isinstance(parsed_command_node, CommandInvocationInitial)
            
            input_type = signature.determine_input_type(parsed_command_node)
            
            checking_result.set(previous_output_type.is_subtype(input_type))
            
            if not checking_result.status:
                checking_result.setMessage(
                    f"Input type '{previous_output_type.pattern}' is not compatible with expected input '{input_type.pattern}' for command '{signature.command_name}'."
                )
                return checking_result
                
            current_output_type = signature.determine_output_type(previous_output_type, parsed_command_node)
            previous_output_type = current_output_type
        
        return checking_result


    def __iter__(self):
        self.initialize_check()
        return self
        
    def __next__(self) -> CheckingResult:
        result = self.check_next()
        if result is None:
            raise StopIteration
        return result

    def get_current_pipeline_content_when_error(self) -> str:
        return self.pipeline_nodes[self.current_index - 1].pretty()
