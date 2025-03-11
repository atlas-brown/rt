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

class UserAnnotation:
    def __init__(self, annotation_type: AnnotationType, pattern: str, pipeline_node: PipeNode, command_node: CommandNode):
        self.annotation_type = annotation_type
        self.pattern = pattern
        self.pipeline_node = pipeline_node
        self.command_node = command_node
    
    def __repr__(self):
        return f"{self.annotation_type.name} {self.pattern} {self.pipeline_node.pretty()} {self.command_node.pretty()}"
    


class EnvAnnotation:
    def __init__(self, annotation_type: AnnotationType, var: str, pattern: str, pipeline_node: PipeNode):
        self.annotation_type = annotation_type
        self.var = var
        self.pattern = pattern
        self.pipeline_node = pipeline_node
    
    def __repr__(self):
        return f"{self.annotation_type.name} {self.var} {self.pattern} {self.pipeline_node.pretty()}"
