import sys
from stream.shell_parser import parse_shell_to_asts
from stream.pipeline_parser import PipelineParser
from stream.regular_type import RegularType
from stream.type_checker import TypeChecker
import logging

def main():
    logging.basicConfig(level=logging.DEBUG)
    pipeline_address = './evaluation_pipelines/valid/6.sh'
    # pipeline_address = './evaluation_pipelines/invalid/2_1.sh'

    type_checker = TypeChecker(pipeline_address)
    parsed_pipeline = type_checker.pipeline_parser.parse_pipeline()
    for command in parsed_pipeline:
        logging.debug(command)
    
    return type_checker.check_pipeline()

if __name__ == "__main__":
    main()
