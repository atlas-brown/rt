from enum import Enum
from typing import Optional
from shasta.ast_node import CommandNode, PipeNode


class AnnotationType(Enum):
    ASSUME = "assume"
    ASSERT = "assert"
    EXPECT = "expect"

class UserAnnotation:
    def __init__(self, annotation_type: AnnotationType, pattern: str, pipeline_node: PipeNode, command_node: CommandNode):
        self.annotation_type = annotation_type
        self.pattern = pattern
        self.pipeline_node = pipeline_node
        self.command_node = command_node
    
