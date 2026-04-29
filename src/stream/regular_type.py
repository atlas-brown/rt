import re
import traceback
from typing import Optional, Set, Tuple
from stream.regex_parser import CharacterClass, Dot, EmptyLanguageNode, Literal, Range, Repeat, Union, Complement, Concatenate, EndAnchor, Intersection, RegexParser, StartAnchor, ast_to_automaton, Node, ast_to_regex
import logging
from stream.tool_error import ToolError
from stream.utils.function_timer import timer
import jpype.imports
from stream.transducer import add_newline_if_not_end_with_newline_FST, full_stream_to_line_based_FST, product_fst_automaton
from stream.automata_to_regex import automaton_to_ast, get_singleton
if not jpype.isJVMStarted():
    jpype.startJVM(classpath=["jars/automaton.jar"])
from dk.brics.automaton import RegExp, Automaton, BasicOperations, BasicAutomata, SpecialOperations, State, Transition, RegExp # type: ignore
from stream.transducer import process_empty_transitions

no_newline_automaton = ast_to_automaton(RegexParser("[^\\n]*").parse())

alphabet_size = 255
alphabet_automaton = RegExp(f"[{chr(0)}-{chr(alphabet_size)}]*").toAutomaton()

def reverse_automaton(automaton: Automaton) -> Automaton:
        empty_transitions: Set[Tuple[State, State]] = set()
        mapping: dict[State, State] = {}
        out_nfa = Automaton()
        initial_state = out_nfa.getInitialState()
        for state in automaton.getStates():
            mapping[state] = State()
        for state in automaton.getStates():
            if state.isAccept():
                empty_transitions.add((initial_state, mapping[state]))
            for transition in state.getTransitions():
                min_in = transition.getMin()
                max_in = transition.getMax()
                dest = transition.getDest()
                mapping[dest].addTransition(Transition(min_in, max_in, mapping[state]))
        mapping[automaton.getInitialState()].setAccept(True)
        # handle empty transitions
        process_empty_transitions(empty_transitions)
        out_nfa.setDeterministic(False)
        out_nfa.removeDeadTransitions()
        out_nfa.minimize()
        return out_nfa

class RegularType:
    def __init__(
            self, 
            pattern: Optional[str] = None, 
            mode: str = "compat", 
            repr_mode: str = "line",
            automaton: Optional[Automaton] = None,
            hole_dict: Optional[dict[str, 'RegularType']] = None,
            tainted: bool = True,
        ) -> None:
        if pattern is None and automaton is None:
            raise ValueError("Invalid RegularType object, pattern is None and automaton is None")
        
        self.repr_mode = repr_mode
        self.tainted = tainted
        if automaton is not None:
            self.pattern = None
            self.ast = None
            self.nfa = automaton
            self.nfa = self.nfa.intersection(alphabet_automaton)
            if repr_mode == "line":
                self.nfa = self.nfa.intersection(no_newline_automaton)
            return
        if pattern is not None and "\\n" in pattern:
            self.repr_mode = "stream"
        self.pattern = pattern
        self.ast = RegexParser(preprocess(self.pattern), mode).parse()
        if mode == "basic":
            self.pattern = ast_to_regex(self.ast)
        if hole_dict is not None:
            automaton_dict = {k: v.nfa for k, v in hole_dict.items()}
        else:
            automaton_dict = None
        self.nfa = ast_to_automaton(self.ast, hole_dict=automaton_dict)
        self.nfa = self.nfa.intersection(alphabet_automaton)
        if self.repr_mode == "line":
            self.nfa = self.nfa.intersection(no_newline_automaton)

    def empty_intersection(self, other: 'RegularType') -> bool:
        return self.nfa.intersection(other.nfa).isEmpty()

    def not_subtype(self, other: 'RegularType', enable_witness: bool = True) -> Tuple[bool, str | None]:
        result, witness = self.is_subtype(other, enable_witness=enable_witness)
        return not result, witness
    
    def get_shortest_example(self) -> str:
        return str(self.nfa.getShortestExample(True))
    
    def is_subtype(self, other: 'RegularType', enable_timeout: bool = False, timeout: int = 10, enable_witness: bool = True) -> Tuple[bool, str | None]:
        if self.repr_mode == "stream" or other.repr_mode == "stream":
            a = self.to_full_stream_repr().nfa
            a = a.intersection(ast_to_automaton(RegexParser(".+").parse()))
            a = product_fst_automaton(add_newline_if_not_end_with_newline_FST(), a)
            b = other.to_full_stream_repr().nfa
            b = b.intersection(ast_to_automaton(RegexParser(".+").parse()))
            b = product_fst_automaton(add_newline_if_not_end_with_newline_FST(), b)
        else:
            a = self.nfa
            b = other.nfa
        logging.debug("checking subsumption")
        is_subtype = a.subsetOf(b)
        witness = None

        if not is_subtype and enable_witness:
            logging.debug("generating counterexample")
            diff_nfa = a.minus(b)
            print_diff_nfa = diff_nfa.intersection(ast_to_automaton(RegexParser("[[:print:]]*").parse()))
            no_newline_diff_nfa = print_diff_nfa.intersection(ast_to_automaton(RegexParser("[^\\n]*").parse()))
            if not no_newline_diff_nfa.isEmpty():
                counterexample = str(no_newline_diff_nfa.getShortestExample(True))
            elif not print_diff_nfa.isEmpty():
                counterexample = str(print_diff_nfa.getShortestExample(True))
            else:
                counterexample = str(diff_nfa.getShortestExample(True))
            escaped_counterexample = ""
            for c in counterexample:
                if c == "\n":
                    escaped_counterexample += "\\n"
                elif c == "\t":
                    escaped_counterexample += "\\t"
                elif c == "\r":
                    escaped_counterexample += "\\r"
                else:
                    escaped_counterexample += c
            witness = escaped_counterexample

        return is_subtype, witness

    def is_empty(self) -> bool:
        logging.debug("checking emptiness")
        return self.to_line_based_repr().nfa.isEmpty()
    
    def is_empty_string(self) -> bool:
        logging.debug("checking empty string")
        return self.to_line_based_repr().nfa.isEmptyString()
    
    @timer
    def to_full_stream_repr(self) -> "RegularType":
        if self.repr_mode == "stream":
            return self
        if self.repr_mode == "line":
            # (r\n)*(r\n?)?
            line_nfa = self.nfa.intersection(ast_to_automaton(RegexParser("[^\\n]*").parse()))
            nfa = BasicOperations.concatenate(line_nfa, BasicAutomata.makeChar('\n'))
            nfa = BasicOperations.repeat(nfa, 0)

            nfa2 = BasicOperations.concatenate(line_nfa, BasicOperations.repeat(BasicAutomata.makeChar('\n'), 0, 1))
            nfa2 = BasicOperations.repeat(nfa2, 0, 1)
            nfa = BasicOperations.concatenate(nfa, nfa2)
            nfa.setDeterministic(False)
            nfa.removeDeadTransitions()
            nfa.minimize()
            return RegularType(automaton=nfa, repr_mode="stream", tainted=self.tainted)

    def to_one_line_repr(self) -> "RegularType":
        if self.repr_mode == "line":
            line_nfa = self.nfa.intersection(ast_to_automaton(RegexParser("[^\\n]*").parse()))
            nfa = BasicOperations.concatenate(line_nfa, BasicAutomata.makeChar('\n'))
            return RegularType(automaton=nfa, repr_mode="stream", tainted=True)
        else:
            return self

    def to_one_line_without_newline_repr(self) -> "RegularType":
        if self.repr_mode == "line":
            line_nfa = self.nfa.intersection(ast_to_automaton(RegexParser("[^\\n]*").parse()))
            return RegularType(automaton=line_nfa, repr_mode="stream", tainted=True)
        else:
            return self

    @timer
    def to_line_based_repr(self) -> "RegularType":
        if self.repr_mode == "line":
            return self
        if self.repr_mode == "stream":
            fst = full_stream_to_line_based_FST()
            nfa = product_fst_automaton(fst, self.nfa)
            return RegularType(automaton=nfa, repr_mode="line", tainted=True)


    def __le__(self, other: 'RegularType') -> bool:
        is_subtype, _ = self.is_subtype(other, enable_witness=False)
        return is_subtype
    
    def __ge__(self, other: 'RegularType') -> bool:
        is_subtype, _ = other.is_subtype(self, enable_witness=False)
        return is_subtype
    
    def __add__(self, other: 'RegularType') -> 'RegularType':
        a = self.to_line_based_repr().nfa
        b = other.to_line_based_repr().nfa
        out = RegularType(automaton=BasicOperations.concatenate(a, b))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        if self.pattern is not None and other.pattern is not None:
            out.pattern = f"({self.pattern})({other.pattern})"
        out.tainted = self.tainted or other.tainted
        return out
    
    def __sub__(self, other: 'RegularType') -> 'RegularType':
        a = self.to_line_based_repr().nfa
        b = other.to_line_based_repr().nfa
        out = RegularType(automaton=BasicOperations.minus(a, b))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        out.tainted = self.tainted or other.tainted
        return out

    def __and__(self, other: 'RegularType') -> 'RegularType':
        a = self.to_line_based_repr().nfa
        b = other.to_line_based_repr().nfa
        out = RegularType(automaton=BasicOperations.intersection(a, b))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        if self.pattern is not None and other.pattern is not None:
            out.pattern = f"({self.pattern})&({other.pattern})"
        out.tainted = self.tainted or other.tainted
        return out
    
    def __or__(self, other: 'RegularType') -> 'RegularType':
        a = self.to_line_based_repr().nfa
        b = other.to_line_based_repr().nfa
        out = RegularType(automaton=BasicOperations.union(a, b))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        if self.pattern is not None and other.pattern is not None:
            out.pattern = f"({self.pattern})|({other.pattern})"
        out.tainted = self.tainted or other.tainted
        return out
    
    def __invert__(self) -> 'RegularType':
        a = self.to_line_based_repr().nfa
        out = RegularType(automaton=BasicOperations.minus(no_newline_automaton, a))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        if self.pattern is not None:
            out.pattern = f"~({self.pattern})"
        out.tainted = self.tainted
        return out
    
    def optional(self) -> 'RegularType':
        a = self.to_line_based_repr().nfa
        out = RegularType(automaton=BasicOperations.optional(a))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        if self.pattern is not None:
            out.pattern = f"({self.pattern})?"
        out.tainted = self.tainted
        return out
    
    def kleene_star(self) -> 'RegularType':
        a = self.to_line_based_repr().nfa
        out = RegularType(automaton=BasicOperations.repeat(a, 0))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        if self.pattern is not None:
            out.pattern = f"({self.pattern})*"
        out.tainted = self.tainted
        return out
    
    def kleene_plus(self) -> 'RegularType':
        a = self.to_line_based_repr().nfa
        out = RegularType(automaton=BasicOperations.repeat(a, 1))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        if self.pattern is not None:
            out.pattern = f"({self.pattern})+"
        out.tainted = self.tainted
        return out
    

    def reverse(self) -> 'RegularType':
        a = self.to_line_based_repr().nfa
        out_nfa = reverse_automaton(a)
        reverse = RegularType(automaton=out_nfa)
        if self.pattern is not None:
            reverse.pattern = f"({self.pattern})^R"
        reverse.tainted = self.tainted
        return reverse


    def __repr__(self) -> str:
       if self.pattern is None:
           return "RegularType(Automaton)\n" + str(self.nfa)
       return f"RegularType({self.pattern})"
    
    @timer
    def get_singleton(self) -> Optional[str]:
        singleton = get_singleton(self.nfa)
        if singleton is not None:
            escaped_singleton = ""
            for c in singleton:
                if c == "\n":
                    escaped_singleton += "\\n"
                elif c == "\t":
                    escaped_singleton += "\\t"
                elif c == "\r":
                    escaped_singleton += "\\r"
                elif c ==".":
                    escaped_singleton += "\\."
                elif c == "\\":
                    escaped_singleton += "\\\\"
                elif c == "|":
                    escaped_singleton += "\\|"
                elif c == "(":
                    escaped_singleton += "\\("
                elif c == ")":
                    escaped_singleton += "\\)"
                elif c == "*":
                    escaped_singleton += "\\*"
                elif c == "+":
                    escaped_singleton += "\\+"
                elif c == "?":
                    escaped_singleton += "\\?"
                elif c == "[":
                    escaped_singleton += "\\["
                elif c == "]":
                    escaped_singleton += "\\]"
                elif c == "{":
                    escaped_singleton += "\\{"
                elif c == "}":
                    escaped_singleton += "\\}"
                else:
                    escaped_singleton += c
            return escaped_singleton
        return None

    @timer
    def to_regex(self) -> str:
        """Convert automaton to a regular expression string."""
            
        try:
            ast = automaton_to_ast(self.nfa)
            regex_str: str = ast_to_regex(ast)
            
            # Escape non-printable characters
            escaped_chars_list = []
            for char in regex_str:
                if char == '\t':
                    escaped_chars_list.append('\\t')
                elif char == '\n':
                    escaped_chars_list.append('\\n')
                else:
                    if char.isprintable():
                        escaped_chars_list.append(char)
                    else:
                        codepoint = ord(char)
                        escaped_chars_list.append(f"\\u{codepoint:04x}")
            escaped_str = "".join(escaped_chars_list)
                    
            return escaped_str
        except Exception as e:
            traceback.print_exc()
            exit()


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
def preprocess(pattern: str) -> str:
    # process replacement(${A} to (.*)) 
    replace_pattern = r'\$\{[^}]*\}|\$\([^)]*\)|\\\$\\\{[^}]*\\\}|\\\$\\\([^)]*\\\)'
    pattern = re.sub(replace_pattern, r'(.*)', pattern)
    # ?! -> ~
    replace_pattern = r'\(\?!'
    pattern = re.sub(replace_pattern, r'~(', pattern)
    return pattern
        
