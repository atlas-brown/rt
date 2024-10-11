from stream.regular_type import RegularType
from stream.pipeline_parser import PipelineParser
from typing import Any, Dict, List
from stream.command_signature import CommandSignature


class TypeChecker:
    def __init__(self, pipeline_address: str) -> None:
        self.pipeline_parser = PipelineParser(pipeline_address)

    def check_pipeline(self) -> bool:
        parsed_commands = self.pipeline_parser.parse_pipeline()
        previous_output_type = RegularType("") # start with empty type

        for parsed_command in parsed_commands:
            signature: 'CommandSignature' = parsed_command['signature']
            parsed_args: Dict[str, List[str]] = parsed_command['parsed_args']
            parsed_flags: List[str] = parsed_command['parsed_flags']

            if not previous_output_type.is_subtype(signature.default_input_type):
                print(
                    f"Input type '{previous_output_type.pattern}' is not compatible with expected input '{signature.default_input_type.pattern}' for command '{signature.command_name}'."
                )
                return False
            
            current_output_type = signature.determine_output_type(parsed_flags, parsed_args, previous_output_type)
            previous_output_type = current_output_type

        print("Pipeline is well-typed.")
        return True
