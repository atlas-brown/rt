from stream.type_checker import TypeChecker
import logging

def main():
    logging.basicConfig(level=logging.DEBUG)
    pipeline_address = './evaluation_pipelines/debug.sh'

    with open(pipeline_address, 'r') as f:
        pipeline = f.read()
        logging.debug(pipeline)
        logging.debug("-"*60)

    type_checker = TypeChecker(pipeline_address)
    parsed_pipeline = type_checker.shell_parser.parse_pipeline()
    logging.debug("-"*60)
    for command in parsed_pipeline:
        logging.debug(command)
        logging.debug("-"*60)
    
    for checking_result in type_checker:
        logging.debug(checking_result)
        logging.debug("-"*60)

if __name__ == "__main__":
    main()
