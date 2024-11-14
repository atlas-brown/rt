class CheckingResult:
    def __init__(self, status, pipeNode = None, message: str = None, counterexample: str = None, type_derivation_trace = None):
        self.status = status
        self.pipeNode = pipeNode
        self.message = message
        self.counterexample = counterexample
        self.type_derivation_trace = type_derivation_trace

    def setPipeNode(self, pipeNode):
        self.pipeNode = pipeNode

    def setCouterexample(self, counterexample: str):
        self.counterexample = counterexample

    def setMessage(self, message: str):
        self.message = message

    def __repr__(self):
        return f"CheckingResult({self.pipeNode}\n{self.status}\n{self.message}\n{self.counterexample}\n{self.type_derivation_trace})"