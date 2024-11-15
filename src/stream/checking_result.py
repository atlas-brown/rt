from __future__ import annotations
class CheckingResult:
    def __init__(self, status, pipeNode = None, message: str = None, counterexample: str = None, type_derivation_trace = None):
        self.status = status

        self.pipe_node = None
        self.message = None
        self.counterexample = None
        self.type_derivation_trace = None

        self.pipeline_content = None

        self.setPipeNode(pipeNode)
        self.setMessage(message)
        self.setCounterexample(counterexample)
        self.setTypeDerivationTrace(type_derivation_trace)
    
    def set(self, other: CheckingResult):
        self.status = other.status
        self.setPipeNode(other.pipe_node)
        self.setMessage(other.message)
        self.setCounterexample(other.counterexample)
        self.setTypeDerivationTrace(other.type_derivation_trace)

        
    def setPipeNode(self, pipe_node):
        if pipe_node is not None:
            self.pipe_node = pipe_node
            self.pipeline_content = pipe_node.pretty()

    def setCounterexample(self, counterexample: str):
        if counterexample is not None:
            self.counterexample = counterexample

    def setMessage(self, message: str):
        if message is not None:
            self.message = message

    def setTypeDerivationTrace(self, type_derivation_trace):
        if type_derivation_trace is not None:
            self.type_derivation_trace = type_derivation_trace 

    def __repr__(self):
        return f"CheckingResult(\n{self.pipeline_content}\n{self.status}\n{self.message}\n{self.counterexample}\n{self.type_derivation_trace}\n)"