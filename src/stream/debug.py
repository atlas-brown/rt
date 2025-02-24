import logging
import jpype
import jpype.imports
if not jpype.isJVMStarted():
    jpype.startJVM(classpath=["jars/automaton.jar"])
from stream.type_checker import TypeChecker

def main():
    logging.basicConfig(level=logging.DEBUG)
    pipeline_address = './evaluation_pipelines/debug.sh'
    pipeline_address = './full_benchmark/llm_injection/pipelines/17.sh'

    with open(pipeline_address, 'r') as f:
        pipeline = f.read()
        logging.debug(pipeline)
        logging.debug("-"*60)

    type_checker = TypeChecker(pipeline_address, enable_stage_timeout=True, stage_timeout=20)
    parsed_pipeline = type_checker.shell_parser.parse_pipeline()
    logging.debug("-"*60)
    for command in parsed_pipeline:
        logging.debug(command)
        logging.debug("-"*60)
    
    for checking_result in type_checker:
        logging.debug(checking_result)
        logging.debug("-"*60)

    jpype.shutdownJVM()
if __name__ == "__main__":
    main()
