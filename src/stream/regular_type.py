import re
from typing import Optional, Set, Tuple
import z3
from stream.regex_parser import Union, Complement, Concatenate, EndAnchor, Intersection, RegexParser, StartAnchor, ast_to_automaton, ast_to_z3, Node, ast_to_regex
import logging
from stream.checking_result import CheckingResult
from stream.tool_error import TimeoutError, ToolError
from stream.utils.timing import Timing
import jpype.imports
from stream.transducer import full_stream_to_line_based_FST, product_fst_automaton
if not jpype.isJVMStarted():
    jpype.startJVM(classpath=["jars/automaton.jar"])
from dk.brics.automaton import RegExp, Automaton, BasicOperations, BasicAutomata, SpecialOperations, State, Transition # type: ignore
from stream.transducer import process_empty_transitions

class RegularType:
    def __init__(
            self, 
            pattern: Optional[str] = None, 
            mode: str = "compat", 
            repr_mode: str = "line",
            automaton: Optional[Automaton] = None,
            hole_dict: Optional[dict[str, 'RegularType']] = None,
            possible_line_numbers: Tuple[int, int] = (0, -1),
            tainted: bool = True
        ) -> None:
        if pattern is None and automaton is None:
            raise ValueError("Invalid RegularType object, pattern is None and automaton is None")
        
        self.repr_mode = repr_mode
        # FIXME: provisional solution
        self.possible_line_numbers = possible_line_numbers
        self.tainted = tainted
        if automaton is not None:
            self.pattern = None
            self.ast = None
            self.nfa = automaton
            return
        if pattern.endswith("\\n") and pattern.count("\\n") == 1:
            self.pattern = pattern[:-2]
            self.possible_line_numbers = (0, 1)
        else:
            self.pattern = pattern
        self.ast = RegexParser(preprocess(self.pattern), mode).parse()
        if hole_dict is not None:
            automaton_dict = {k: v.nfa for k, v in hole_dict.items()}
        else:
            automaton_dict = None
        self.nfa = ast_to_automaton(self.ast, hole_dict=automaton_dict)
    def is_subtype(self, other: 'RegularType', enable_timeout: bool = False, timeout: int = 10) -> CheckingResult:
        logging.debug("-"*60)
        # logging.debug(f"checking: {self.pattern} is subtype of {other.pattern}")
        # logging.debug(f"self_regex: {self.regex}")
        # logging.debug(f"other_regex: {other.regex}")
        # logging.debug(f"self_ast: {self.ast}")
        # logging.debug(f"other_ast: {other.ast}")
        if self.possible_line_numbers[0] < other.possible_line_numbers[0]:
            return CheckingResult(ill_typed=True)
        if other.possible_line_numbers[1] != -1 and (self.possible_line_numbers[1] > other.possible_line_numbers[1] or self.possible_line_numbers[1] == -1):
            return CheckingResult(ill_typed=True)
        logging.debug("-"*60)
        if (other.pattern == ".*"):
            return CheckingResult(ill_typed=False)
        # if (r"\n" in self.pattern) or (r"\n" in other.pattern):
        #     self.to_full_stream_regex()
        #     other.to_full_stream_regex()
        with Timing("timing intersection creation = "):
            # intersection_regex = z3.Intersect(self.regex, z3.Complement(other.regex))
            # # checking_result = CheckingResult(ill_typed=(s.check() == z3.sat))
            # s = z3.Solver()
            # s.add(z3.Distinct(intersection_regex, z3.Intersect(z3.Re("a"), z3.Re("b"))))
            # output = run_z3(s, enable_timeout=enable_timeout, timeout=timeout)
            # # if output == "unknown":
            # #     raise TimeoutError("Timeout in z3")
            # # checking_result = CheckingResult(ill_typed=(output == "sat"))
            # checking_result = CheckingResult(ill_typed=(output == z3.sat))


            logging.debug("checking subsumption")
            checking_result = CheckingResult(ill_typed=not self.nfa.subsetOf(other.nfa))

        if checking_result.ill_typed:
            with Timing(f"timing counterexample gen = "):
                # s = z3.Solver()
                # x = z3.String('x')
                # s.add(z3.InRe(x, intersection_regex))
                # # s.check()
                # # counterexample = s.model()[x].as_string()
                # counterexample = run_z3(s, get_model=True, enable_timeout=enable_timeout, timeout=timeout)
                # checking_result.set_counterexample(counterexample)

                logging.debug("generating counterexample")
                diff_nfa = self.nfa.minus(other.nfa)
                print_diff_nfa = diff_nfa.intersection(ast_to_automaton(RegexParser("[[:print:]]*").parse()))
                if not print_diff_nfa.isEmpty():
                    counterexample = print_diff_nfa.getShortestExample(True)
                else:
                    counterexample = diff_nfa.getShortestExample(True)
                checking_result.set_counterexample(counterexample)

        return checking_result

    def is_empty(self) -> bool:
        # s = z3.Solver()
        # logging.debug(f"checking: {self.pattern} is empty")
        # logging.debug(f"self_regex: {self.regex}")
        # s.add(z3.Distinct(self.regex, z3.Intersect(z3.Re("a"), z3.Re("b"))))
        # output = run_z3(s)
        # return output == z3.unsat

        logging.debug("checking emptiness")
        return self.nfa.isEmpty()
    
    def is_empty_string(self) -> bool:
        # s = z3.Solver()
        # s.add(z3.Distinct(self.regex, z3.Re("")))
        # output = run_z3(s)
        # return output == z3.unsat

        logging.debug("checking empty string")
        return self.nfa.isEmptyString()
    
    def to_full_stream_repr(self) -> "RegularType":
        if self.repr_mode == "full":
            return self
        if self.repr_mode == "line":
            nfa = BasicOperations.concatenate(BasicOperations.Intersection(self.nfa, RegExp("[^\n]*").toAutomaton()), BasicAutomata.makeChar('\n'))
            nfa = BasicOperations.repeat(nfa, 0)
            return RegularType(automaton=nfa)

    def to_line_based_repr(self) -> "RegularType":
        if self.repr_mode == "line":
            return self
        if self.repr_mode == "full":
            fst = full_stream_to_line_based_FST()
            nfa = product_fst_automaton(fst, self.nfa)
            return RegularType(automaton=nfa)


    def __le__(self, other: 'RegularType') -> bool:
        return self.is_subtype(other)
    
    def __ge__(self, other: 'RegularType') -> bool:
        return other.is_subtype(self)
    
    def __add__(self, other: 'RegularType') -> 'RegularType':
        out = RegularType(automaton=BasicOperations.concatenate(self.nfa, other.nfa))
        out.nfa.setDeterministic(False)
        out.nfa.removeDeadTransitions()
        out.nfa.minimize()
        if self.pattern is not None and other.pattern is not None:
            out.pattern = f"({self.pattern})({other.pattern})"
        out.tainted = self.tainted or other.tainted
        return out
    
    def __sub__(self, other: 'RegularType') -> 'RegularType':
        out = RegularType(automaton=BasicOperations.minus(self.nfa, other.nfa))
        out.nfa.setDeterministic(False)
        out.nfa.removeDeadTransitions()
        out.nfa.minimize()
        out.tainted = self.tainted or other.tainted
        return out

    def __and__(self, other: 'RegularType') -> 'RegularType':
        out = RegularType(automaton=BasicOperations.intersection(self.nfa, other.nfa))
        out.nfa.setDeterministic(False)
        out.nfa.removeDeadTransitions()
        out.nfa.minimize()
        if self.pattern is not None and other.pattern is not None:
            out.pattern = f"({self.pattern})&({other.pattern})"
        out.tainted = self.tainted or other.tainted
        return out
    
    def __or__(self, other: 'RegularType') -> 'RegularType':
        out = RegularType(automaton=BasicOperations.union(self.nfa, other.nfa))
        out.nfa.setDeterministic(False)
        out.nfa.removeDeadTransitions()
        out.nfa.minimize()
        if self.pattern is not None and other.pattern is not None:
            out.pattern = f"({self.pattern})|({other.pattern})"
        out.tainted = self.tainted or other.tainted
        return out
    
    def __invert__(self) -> 'RegularType':
        out = RegularType(automaton=BasicOperations.minus(BasicAutomata.makeAnyString(), self.nfa))
        out.nfa.setDeterministic(False)
        out.nfa.removeDeadTransitions()
        out.nfa.minimize()
        if self.pattern is not None:
            out.pattern = f"~({self.pattern})"
        out.tainted = self.tainted
        return out
    
    def optional(self) -> 'RegularType':
        out = RegularType(automaton=BasicOperations.optional(self.nfa))
        out.nfa.setDeterministic(False)
        out.nfa.removeDeadTransitions()
        out.nfa.minimize()
        if self.pattern is not None:
            out.pattern = f"({self.pattern})?"
        out.tainted = self.tainted
        return out
    
    def kleene_star(self) -> 'RegularType':
        out = RegularType(automaton=BasicOperations.repeat(self.nfa, 0))
        out.nfa.setDeterministic(False)
        out.nfa.removeDeadTransitions()
        out.nfa.minimize()
        if self.pattern is not None:
            out.pattern = f"({self.pattern})*"
        out.tainted = self.tainted
        return out
    
    def kleene_plus(self) -> 'RegularType':
        out = RegularType(automaton=BasicOperations.repeat(self.nfa, 1))
        out.nfa.setDeterministic(False)
        out.nfa.removeDeadTransitions()
        out.nfa.minimize()
        if self.pattern is not None:
            out.pattern = f"({self.pattern})+"
        out.tainted = self.tainted
        return out
    

    def reverse(self) -> 'RegularType':
        empty_transitions: Set[Tuple[State, State]] = set()
        mapping: dict[State, State] = {}
        out_nfa = Automaton()
        initial_state = out_nfa.getInitialState()
        for state in self.nfa.getStates():
            mapping[state] = State()
        for state in self.nfa.getStates():
            if state.isAccept():
                empty_transitions.add((initial_state, mapping[state]))
            for transition in state.getTransitions():
                min_in = transition.getMin()
                max_in = transition.getMax()
                dest = transition.getDest()
                mapping[dest].addTransition(Transition(min_in, max_in, mapping[state]))
        mapping[self.nfa.getInitialState()].setAccept(True)
        # handle empty transitions
        process_empty_transitions(empty_transitions)
        out_nfa.setDeterministic(False)
        out_nfa.removeDeadTransitions()
        out_nfa.minimize()
        reverse = RegularType(automaton=out_nfa)
        if self.pattern is not None:
            reverse.pattern = f"({self.pattern})^R"
        reverse.tainted = self.tainted
        return reverse


    def __repr__(self) -> str:
       if self.pattern is None:
           return "RegularType(Automaton)\n" + str(self.nfa)
       return f"RegularType({self.pattern})"


# FIXME: temporary solution, need to be fixed, consider a|^b
def starts_with_start_anchor(pattern: RegularType) -> bool:
    if pattern.ast is None:
        return False
    if isinstance(pattern.ast, Concatenate):
        return isinstance(pattern.ast.nodes[0], StartAnchor)
    return False

def ends_with_end_anchor(pattern: RegularType) -> bool:
    if pattern.ast is None:
        return False
    if isinstance(pattern.ast, Concatenate):
        return isinstance(pattern.ast.nodes[-1], EndAnchor)
    return False

def remove_anchors(pattern: RegularType) -> RegularType:
    if pattern.ast is None:
        return pattern
    if isinstance(pattern.ast, Concatenate):
        if isinstance(pattern.ast.nodes[0], StartAnchor):
            pattern.ast.nodes = pattern.ast.nodes[1:]
        if isinstance(pattern.ast.nodes[-1], EndAnchor):
            pattern.ast.nodes = pattern.ast.nodes[:-1]
    return pattern



# replace ${A} with (.*)  and  $(A) with (.*)
# FIXME ?! is not needed currently, provisonal fix: replace ?! with ~
def preprocess(pattern: str) -> str:
    # process replacement(${A} to (.*)) 
    # FIXME for $(), cannot handle nested brackets, need to be fixed
    replace_pattern = r'\$\{[^}]*\}|\$\([^)]*\)|\\\$\\\{[^}]*\\\}|\\\$\\\([^)]*\\\)'
    pattern = re.sub(replace_pattern, r'(.*)', pattern)
    # ?! -> ~
    replace_pattern = r'\(\?!'
    pattern = re.sub(replace_pattern, r'~(', pattern)
    return pattern


#     if ")&(" not in pattern:
#         return pattern
    

#     intersect_index = pattern.index(")&(")
#     # find ( in the left side
#     left_index = intersect_index
#     open_brackets = 1
#     while left_index >= 1 and open_brackets > 0:
#         left_index -= 1
#         if pattern[left_index] == ")" and (left_index == 0 or pattern[left_index-1] != "\\"):
#             open_brackets += 1
#         elif pattern[left_index] == "(" and (left_index == 0 or pattern[left_index-1] != "\\"):
#             open_brackets -= 1
    
#     if open_brackets != 0:
#         raise ToolError("unmatched brackets at the left side of the intersection")

#     assert pattern[left_index] == "("
    
#     # find ) in the right side
#     right_index = intersect_index + 2
#     open_brackets = 1
#     while right_index < len(pattern) - 1 and open_brackets > 0:
#         right_index += 1
#         if pattern[right_index] == "(" and pattern[right_index-1] != "\\":
#             open_brackets += 1
#         elif pattern[right_index] == ")" and pattern[right_index-1] != "\\":
#             open_brackets -= 1

#     if open_brackets != 0:
#         raise ToolError("unmatched brackets at the right side of the intersection")

#     assert pattern[right_index] == ")"

#     left = pattern[left_index+1:intersect_index]
#     right = pattern[intersect_index+3:right_index]
#     left_rest = pattern[:left_index]
#     right_rest = pattern[right_index+1:]

#     if is_dot_star(left):
#         return preprocess(f"{left_rest}({right}){right_rest}")
#     if is_dot_star(right):
#         return preprocess(f"{left_rest}({left}){right_rest}")

#     # )&( reduces, so the recursive call will eventually terminate
#     return preprocess(f"{left_rest}(?!(?!{left})|(?!{right})){right_rest}")

# def is_dot_star(s: str) -> bool:
#     while len(s) > 0 and s.startswith("(") and s.endswith(")"):
#         s = s[1:-1]
#     return s == ".*"



# def run_z3(solver: z3.Solver, get_model: bool = False, enable_timeout: bool = False, timeout: int = 10) -> z3.CheckSatResult | str:
#     if not enable_timeout:
#         result = solver.check()
#         if get_model and result == z3.sat:
#             return parse_z3_output_model(str(solver.model()))
#         elif get_model and result == z3.unsat:
#             raise Exception("unsat result does not have a model, smt string: " + solver.to_smt2())
#         else:
#             return result
#     smt_string = solver.to_smt2()
#     smt_string = f"(set-option :timeout {timeout * 1000})\n{smt_string}"

#     constraints = z3.parse_smt2_string(smt_string)
#     s = z3.Solver()
#     for c in constraints:
#         s.add(c)
#     result = s.check()
#     if result == z3.unknown:
#         raise TimeoutError("Timeout in z3")
#     if get_model and result == z3.sat:
#         return parse_z3_output_model(str(s.model()))
#     elif get_model and result == z3.unsat:
#         raise Exception("unsat result does not have a model, smt string: " + s.to_smt2())
#     else:
#         return result
    
# def parse_z3_output_model(output: str) -> str:
#     # Example output: '[x = "A"]'
#     if output.startswith("[x = \""):
#         return output[6:-2]
#     else:
#         raise Exception("Model not found in z3 output: " + output)


# def run_external_z3(solver: z3.Solver, get_model: bool = False, enable_timeout: bool = False, timeout: int = 10) -> str:
#     smt_string = solver.to_smt2()
#     output = run_z3_in_shell(smt_string, get_model, enable_timeout, timeout)
#     # if output.startswith("unknown"):
#     #     output = run_z3_with_file(smt_string, get_model, enable_timeout, timeout)
#     return output

# def run_z3_in_shell(smt_string: str, get_model: bool = False, enable_timeout: bool = False, timeout: int = 10) -> str:
#     cmd = ["z3", "-smt2", "-in"]
#     if enable_timeout:
#         smt_string = f"(set-option :timeout {timeout * 1000})\n{smt_string}"
#     if get_model:
#         smt_string = f"{smt_string}(get-model)\n"
#     logging.debug(f"smt2: {smt_string}")
#     logging.debug("calling z3 in shell")
#     kwargs = {
#         "input": smt_string,
#         "text": True,
#         "stdout": subprocess.PIPE,
#         "stderr": subprocess.PIPE,
#     }
#     result = subprocess.run(cmd, **kwargs)
#     return result.stdout.strip()

# def run_z3_with_file(smt_string: str, get_model: bool = False, enable_timeout: bool = False, timeout: int = 10) -> str:
#     with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as f:
#         if enable_timeout:
#             smt_string = f"(set-option :timeout {timeout * 1000})\n{smt_string}"
#         if get_model:
#             smt_string = f"{smt_string}(get-model)\n"
#         f.write(smt_string)
#         f.flush()
#         cmd = ["z3", "-smt2", f.name]
#         logging.debug(f"calling z3 with file: {f.name}")
#         result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#         return result.stdout.strip()

# def parse_external_z3_output_model(output: str) -> Optional[str]:
#     """
#     Example output:
#     sat
#     (
#     (define-fun x () String
#         "")
#     )
#     """
#     if output == "unknown":
#         raise TimeoutError("Timeout in z3")
#     pattern = re.compile(
#         r'\(define-fun\s+x\s+\(\)\s+String\s+"(.*?)"\)', re.DOTALL)
#     match = pattern.search(output)
#     if match:
#         return match.group(1)
#     return None
    
    

        

        
        
