import json
from typing import List, Dict, Tuple, Any
from enum import Enum
from reporter import Report, ShseerResult
from dataclasses import dataclass

# Struct to allow serialization
class ClassEncoder(json.JSONEncoder):
    def default(self, o):
            return o.__dict__

class ErrorPoint(json.JSONEncoder):
    cmd: str
    instances: int
    examples: List[str]

    def __init__(self, cmd: str, example: str):
        self.cmd = cmd
        self.instances = 1
        self.examples = [example]
    
    def insert_example(self, example: str):
        self.instances += 1
        self.examples.append(example)
    
    def serialize(self) -> str:
        return json.dumps(self.__dict__, indent=" ", cls=ClassEncoder)

class ErrorSummary(json.JSONEncoder):

    def add_reason(self, data: List[Tuple[str, str]], file):
        for grouping in data:
            if grouping[0] not in self.reasons:
                self.reasons[grouping[0]] = 0
                self.reasons_whom[grouping[0]] = []
                self.reason_pair[grouping[0]] = grouping[1]
            self.reasons[grouping[0]] += 1
            self.reasons_whom[grouping[0]].append(file)
    
    def add_error_msg(self, data: List[str]):
        for msg in data:
            if msg.startswith("('command substitution'"):
                msg = "('command substitution',"
            if msg.startswith("('weird object'"):
                msg = "('weird object',"
            if msg not in self.errors:
                self.errors[msg.strip()] = 0
            self.errors[msg.strip()] += 1

    def add_form(self, data: List[str]):
        for msg in data:
            if msg not in self.forms:
                self.forms[msg.strip()] = 0
            self.forms[msg.strip()] += 1
    
    def add_time(self, data):
        if data is not None:
            self.time.append(data)

    def __init__(self):
        self.reasons: Dict[str, int] = {}
        self.reason_pair: Dict[str, str] = {}
        self.reasons_whom: Dict[str, List[str]] = {}
        self.errors: Dict[str, int] = {}
        self.forms: Dict[str, int] = {}
        self.good_script: List[str] = []
        self.bad_script: List[str] = []
        self.panic_script: List[str] =[]
        self.parse_script : List[str] = []
        self.unknown_script : List[str] = []
        self.crashed_script: List[Dict[str, str]] =[]
        self.timeout_script: List[str] = []
        self.time: List[Any] = []
        self.good: int = 0 
        self.bad: int = 0 
        self.panic: int = 0 
        self.crash: int = 0 
        self.timeout: int = 0 
        self.parse : int = 0 
        self.unknown: int = 0 

    def add_good(self, path: str):
        self.good += 1
        self.good_script.append(path)
    
    def add_parse(self,path:str):
        self.parse += 1
        self.parse_script.append(path)
        
    def add_unknown(self,path:str):
        self.unknown+=1
        self.unknown_script.append(path)

    def add_bad(self, path: str):
        self.bad += 1
        self.bad_script.append(path)

    def add_timeout(self, path: str):
        self.timeout += 1
        self.timeout_script.append(path)

    def add_panic(self, path: str):
        self.panic += 1
        self.panic_script.append(path)

    def add_crash(self, path: str, reason: str):
        self.crash += 1
        explain = {path: reason}
        self.crashed_script.append(explain)

    def serialize(self) -> str:
        return json.dumps(self.__dict__, indent=" ", cls=ClassEncoder)



class VersionBenchmark(json.JSONEncoder):

    # Initialize using the version, [good, bad, panic, timeout, crash], and average time per line of code in ms
    def __init__(self, version: str,  scripts_good: int,scripts_bad: int,scripts_panic: int,scripts_crash: int,scripts_timeout: int,scripts_parse:int,scripts_unknown:int, time_line: float, time_script: float):
        self.version = version
        self.scripts_total = sum([scripts_good, scripts_bad, scripts_panic, scripts_crash, scripts_timeout, scripts_parse, scripts_unknown])
        self.scripts_good = scripts_good
        self.scripts_bad = scripts_bad
        self.scripts_panic = scripts_panic
        self.scripts_timeout = scripts_timeout
        self.scripts_crash = scripts_crash
        self.scripts_parse = scripts_parse
        self.scripts_unknown = scripts_unknown
        self.average_time_per_line = time_line
        self.average_time_per_script = time_script
        self.included = []

    def serialize(self) -> str:
        return json.dumps(self.__dict__, indent=" ", cls=ClassEncoder)

    def debug(self):
        print(self.serialize())