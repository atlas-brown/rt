import json
from shseer.symb_result import ShseerResult
from typing import Any, List

class Report:
    filename: str
    error_messages: list[tuple[str,str]]
    unimplemented_messages: list[str]
    expansion_forms: list[str]
    judgement: ShseerResult
    time: Any

    def __init__(self, all_data: str | None):
        self.filename = ""
        self.error_messages = []
        self.unimplemented_messages = []
        self.expansion_forms = []
        self.judgement = ShseerResult.UNKNOWN
        self.time = None
        if all_data is not None: # try load json
            tokens: List[str] = all_data.split("\n")
            data = {}
            for line in tokens:
                if line.startswith("{"):
                    data = json.loads(line)
                    break
            if "filename" in data:
                self.filename = data["filename"]
            if "error_messages" in data:
                self.error_messages = data["error_messages"]
            if "unimplemented" in data:
                self.unimplemented_messages = data["unimplemented"]
            if "result" in data:
                self.judgement = eval(f"ShseerResult.{data['result']}")
            if "expansion_forms" in data:
                self.expansion_forms = data["expansion_forms"]
            if "time" in data:
                self.time = data["time"]
