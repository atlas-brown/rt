from shasta.ast_node import PipeNode, CommandNode

def pretty_pipe_node(pipe_node: PipeNode) -> str:
    assert isinstance(pipe_node, PipeNode)
    pipeline_str = pipe_node.pretty()
    pipeline_str = pipeline_str.replace("\\\\", "\\")
    return pipeline_str

def pretty_command_node(command_node: CommandNode) -> str:
    assert isinstance(command_node, CommandNode)
    command_str = command_node.pretty()
    command_str = command_str.replace("\\\\", "\\")
    return command_str