from enum import Enum
from typing import Optional
from shasta.ast_node import CommandNode, PipeNode


class AnnotationType(Enum):
    ASSUME = "assume"
    ASSERT = "assert"
    EXPECT = "expect"
    INPUT = "input"
    OUTPUT = "output"
    VAR = "var"
    FILE = "file"
    ASSERT_CONTAINS = "assert_contains"
    OUTPUT_CONTAINS = "output_contains"
class UserAnnotation:
    def __init__(self, annotation_type: AnnotationType, pattern: str, pipeline_node: PipeNode, command_node: CommandNode, annotation_str: str):
        self.annotation_type = annotation_type
        self.pattern = pattern
        self.pipeline_node = pipeline_node
        self.command_node = command_node
        self.annotation_str = annotation_str
    def __repr__(self):
        return self.annotation_str
    


class EnvAnnotation:
    def __init__(self, annotation_type: AnnotationType, var: str, pattern: str, pipeline_node: PipeNode, annotation_str: str):
        self.annotation_type = annotation_type
        self.var = var
        self.pattern = pattern
        self.pipeline_node = pipeline_node
        self.annotation_str = annotation_str
    def __repr__(self):
        return self.annotation_str
