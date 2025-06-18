from shasta.ast_node import PipeNode

def pretty_pipe_node(pipe_node: PipeNode) -> str:
    assert isinstance(pipe_node, PipeNode)
    pipeline_str = pipe_node.pretty()
    pipeline_str = pipeline_str.replace("\\\\", "\\")
    return pipeline_str