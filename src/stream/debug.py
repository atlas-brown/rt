import logging
import jpype
import jpype.imports
if not jpype.isJVMStarted():
    jpype.startJVM(classpath=["jars/automaton.jar"])
from stream.type_checker import TypeChecker
import argparse
import tempfile
import os
from stream.config import CONFIG


def check_pipeline(file_path: str, shellcheck : bool = False):
    type_checker = TypeChecker(file_path, enable_stage_timeout=True, stage_timeout=20)
    parsed_pipeline = type_checker.shell_parser.parse_pipeline()
    logging.debug("-"*60)
    for command in parsed_pipeline:
        logging.debug(command)
        logging.debug("-"*60)
    logging.debug("\n\n\nTypechecking results:")
    for checking_result in type_checker:
        logging.debug(checking_result)
        logging.debug("-"*60)

    if shellcheck:
        logging.debug("Running shellcheck...")
        with tempfile.NamedTemporaryFile(delete=True, suffix='.sh') as temp_file:
            for pipeline in type_checker.shell_parser.pipeline_nodes:
                temp_file.write(pipeline.pretty().encode())
            temp_file.flush()
            os.system(f"shellcheck {temp_file.name}")

def main():
    parser = argparse.ArgumentParser(description="Debug Stream Type Checker")
    parser.add_argument('-f', '--file', type=str, default='./evaluation_pipelines/debug.sh', help="Path to the pipeline file")
    parser.add_argument('-s', '--stdin', action='store_true', help="Read pipeline from stdin")
    parser.add_argument('-d', '--disable-annotations', action='store_true', help="Disable annotations in the type checker")
    parser.add_argument('-c', '--shellcheck', action='store_true', help="Run shellcheck on the pipeline file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)
    if args.disable_annotations:
        logging.info("Annotations are disabled.")
        CONFIG["enable_user_annotation"] = False
    
    if args.stdin:
        logging.info("Reading pipeline from stdin... Hit Ctrl+D to finish input.")
        pipeline = ""
        while True:
            try:
                pipeline = input()
                if pipeline:
                    with tempfile.NamedTemporaryFile(delete=True, suffix='.sh') as temp_file:
                        temp_file.write(pipeline.encode())
                        check_pipeline(temp_file.name, args.shellcheck)
            except EOFError:
                break
    else:
        logging.info(f"Reading pipeline from file: {args.file}")
        check_pipeline(args.file, args.shellcheck)

    jpype.shutdownJVM()

if __name__ == "__main__":
    main()
