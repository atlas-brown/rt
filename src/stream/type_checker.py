import logging
from stream.regular_type import RegularType
from stream.pipeline_parser import PipelineParser
from typing import Any, Dict, List, Tuple
from stream.command_signature import CommandSignature
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from stream.checking_result import CheckingResult

class TypeChecker:
    def __init__(self, pipeline_address: str) -> None:
        self.pipeline_parser = PipelineParser(pipeline_address)

    def check_pipeline(self) -> list[CheckingResult]:
        pipelines = self.pipeline_parser.parse_pipeline()
        pipeline_nodes = self.pipeline_parser.pipeline_nodes
        previous_output_type = RegularType("") # start with empty string type

        checking_results = []

        for parsed_commands, pipeline_node in zip(pipelines, pipeline_nodes):
            for parsed_command in parsed_commands:

                signature, parsed_command_node = parsed_command

                # assert isinstance(signature, CommandSignature)
                assert isinstance(parsed_command_node, CommandInvocationInitial)
                
                input_type = signature.determine_input_type(parsed_command_node)

                checking_result = input_type.is_subtype(previous_output_type)
                checking_result.setPipeNode(pipeline_node)

                if not checking_result.status:
                    checking_result.setMessage(
                        f"Input type '{previous_output_type.pattern}' is not compatible with expected input '{input_type.pattern}' for command '{signature.command_name}'."
                    )
                    checking_results.append(checking_result)
                    break

                current_output_type = signature.determine_output_type(previous_output_type, parsed_command_node)
                previous_output_type = current_output_type

        return checking_results
