from stream.shell_parser import parse_shell_to_asts
from stream.pipeline_parser import PipelineParser
from stream.regular_type import RegularType
from stream.type_checker import TypeChecker

def main():
    pipeline_address = './evaluation_pipelines/valid/6.sh'
    type_checker = TypeChecker(pipeline_address)
    
    parsed_pipeline = type_checker.pipeline_parser.parse_pipeline()
    for command in parsed_pipeline:
        print(command)
    
    type_checker.check_pipeline()

if __name__ == "__main__":
    main()
