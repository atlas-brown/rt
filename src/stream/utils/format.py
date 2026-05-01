from shasta.ast_node import AstNode

def pretty_ast_node(ast_node: AstNode) -> str:
    pipeline_str = ast_node.pretty()
    pipeline_str = pipeline_str.replace("\\\\", "\\")
    return pipeline_str