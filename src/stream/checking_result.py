from __future__ import annotations
class CheckingResult:
    def __init__(self, ill_typed, pipeNode = None, message: str = None, counterexample: str = None, type_derivation_trace = None, tainted: bool = True):
        self.ill_typed: bool = ill_typed

        self.pipe_node = None
        self.message = None
        self.counterexample = None
        self.type_derivation_trace = None

        self.pipeline_content = None

        self.tainted = tainted

        self.set_pipe_node(pipeNode)
        self.set_message(message)
        self.set_counterexample(counterexample)
        self.set_type_derivation_trace(type_derivation_trace)
    
    def set(self, other: CheckingResult):
        self.ill_typed = other.ill_typed
        self.set_pipe_node(other.pipe_node)
        self.set_message(other.message)
        self.set_counterexample(other.counterexample)
        self.set_type_derivation_trace(other.type_derivation_trace)

    def set_ill_typed(self, ill_typed: bool):
        self.ill_typed = ill_typed
        
    def set_pipe_node(self, pipe_node):
        if pipe_node is not None:
            self.pipe_node = pipe_node
            self.pipeline_content = pipe_node.pretty()

    def set_counterexample(self, counterexample: str):
        if counterexample is not None:
            self.counterexample = counterexample

    def set_message(self, message: str):
        if message is not None:
            self.message = message

    def set_type_derivation_trace(self, type_derivation_trace):
        if type_derivation_trace is not None:
            self.type_derivation_trace = type_derivation_trace 

    def __repr__(self):
        return f"CheckingResult(\npipeline content: {self.pipeline_content}\nill_typed?: {self.ill_typed}\nerror message: {self.message}\ncounterexample: {self.counterexample}\nderivation trace: {self.type_derivation_trace}\n)\ntainted: {self.tainted}"