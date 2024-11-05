import logging
from stream.regular_type import RegularType
from stream.pipeline_parser import PipelineParser
from typing import Any, Dict, List, Tuple
from stream.command_signature import CommandSignature
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial


class TypeChecker:
    def __init__(self, pipeline_address: str) -> None:
        self.pipeline_parser = PipelineParser(pipeline_address)

    def check_pipeline(self) -> Tuple[bool, str|None]:
        parsed_commands = self.pipeline_parser.parse_pipeline()
        previous_output_type = RegularType("") # start with empty type

        for parsed_command in parsed_commands:

            signature, parsed_command_node = parsed_command

            # assert isinstance(signature, CommandSignature)
            assert isinstance(parsed_command_node, CommandInvocationInitial)
            
            input_type = signature.determine_input_type(parsed_command_node)

            if not previous_output_type.is_subtype(input_type):
                logging.info(
                    f"Input type '{previous_output_type.pattern}' is not compatible with expected input '{input_type.pattern}' for command '{signature.command_name}'."
                )
                return False, f"Input type '{previous_output_type.pattern}' is not compatible with expected input '{input_type.pattern}' for command '{signature.command_name}'"

            current_output_type = signature.determine_output_type(previous_output_type, parsed_command_node)
            previous_output_type = current_output_type

        logging.info("Pipeline is well-typed.")
        return True, None
