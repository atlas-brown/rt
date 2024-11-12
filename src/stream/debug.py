from stream.shell_parser import parse_shell_to_asts
from stream.pipeline_parser import PipelineParser
from stream.regular_type import RegularType
from stream.type_checker import TypeChecker
from stream.symb import get_raw_nodes, nodes_from_file
import logging

def main():
    logging.basicConfig(level=logging.DEBUG)
    pipeline_address = './evaluation_pipelines/debug.sh'

    with open(pipeline_address, 'r') as f:
        pipeline = f.read()
        logging.debug(pipeline)
        logging.debug("-"*60)

    type_checker = TypeChecker(pipeline_address)
    parsed_pipeline = type_checker.pipeline_parser.parse_pipeline()
    logging.debug("-"*60)
    for command in parsed_pipeline:
        logging.debug(command)
        logging.debug("-"*60)
    
    type_checker.check_pipeline()

if __name__ == "__main__":
    main()
