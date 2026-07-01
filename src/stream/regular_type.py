import logging
from typing import Optional, Tuple

from stream.automata_to_regex import automaton_to_regex, get_singleton
from stream.automaton_utils import reverse_automaton
from stream.constants import (
    alphabet_automaton,
    get_readable_automata_repr_enabled,
    no_newline_automaton,
)
from stream.java_api import Automaton, BasicOperations
from stream.regex_parser import Concatenate, EndAnchor, RegexParser, StartAnchor, ast_to_automaton, ast_to_regex, preprocess
from stream.tool_error import ToolError
from stream.utils.function_timer import timer


class RegularType:
    def __init__(
            self, 
            pattern: Optional[str] = None, 
            mode: str = "compat", 
            automaton: Optional[Automaton] = None,
            hole_dict: Optional[dict[str, 'RegularType']] = None,
            tainted: bool = True,
        ) -> None:
        if pattern is None and automaton is None:
            raise ValueError("Invalid RegularType object, pattern is None and automaton is None")
        
        self.tainted = tainted
        if automaton is not None:
            self.pattern = None
            self.ast = None
            self.nfa = automaton
            self.nfa = self.nfa.intersection(alphabet_automaton)
            self.nfa = self.nfa.intersection(no_newline_automaton)
            return
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
        self.nfa = self.nfa.intersection(no_newline_automaton)

    def empty_intersection(self, other: 'RegularType') -> bool:
        return self.nfa.intersection(other.nfa).isEmpty()

    def not_subtype(self, other: 'RegularType', enable_witness: bool = True) -> Tuple[bool, str | None]:
        result, witness = self.is_subtype(other, enable_witness=enable_witness)
        return not result, witness
    
    def get_shortest_example(self) -> str:
        return str(self.nfa.getShortestExample(True))
    
    def is_subtype(self, other: 'RegularType', enable_timeout: bool = False, timeout: int = 10, enable_witness: bool = True) -> Tuple[bool, str | None]:
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
        return self.nfa.isEmpty()
    
    def is_empty_string(self) -> bool:
        logging.debug("checking empty string")
        return self.nfa.isEmptyString()
    
    def __le__(self, other: 'RegularType') -> bool:
        is_subtype, _ = self.is_subtype(other, enable_witness=False)
        return is_subtype
    
    def __ge__(self, other: 'RegularType') -> bool:
        is_subtype, _ = other.is_subtype(self, enable_witness=False)
        return is_subtype
    
    def __add__(self, other: 'RegularType') -> 'RegularType':
        a = self.nfa
        b = other.nfa
        out = RegularType(automaton=BasicOperations.concatenate(a, b))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        if self.pattern is not None and other.pattern is not None:
            out.pattern = f"({self.pattern})({other.pattern})"
        out.tainted = self.tainted or other.tainted
        return out
    
    def __sub__(self, other: 'RegularType') -> 'RegularType':
        a = self.nfa
        b = other.nfa
        out = RegularType(automaton=BasicOperations.minus(a, b))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        out.tainted = self.tainted or other.tainted
        return out

    def __and__(self, other: 'RegularType') -> 'RegularType':
        a = self.nfa
        b = other.nfa
        out = RegularType(automaton=BasicOperations.intersection(a, b))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        if self.pattern is not None and other.pattern is not None:
            out.pattern = f"({self.pattern})&({other.pattern})"
        out.tainted = self.tainted or other.tainted
        return out
    
    def __or__(self, other: 'RegularType') -> 'RegularType':
        a = self.nfa
        b = other.nfa
        out = RegularType(automaton=BasicOperations.union(a, b))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        if self.pattern is not None and other.pattern is not None:
            out.pattern = f"({self.pattern})|({other.pattern})"
        out.tainted = self.tainted or other.tainted
        return out
    
    def __invert__(self) -> 'RegularType':
        a = self.nfa
        out = RegularType(automaton=BasicOperations.minus(no_newline_automaton, a))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        if self.pattern is not None:
            out.pattern = f"~({self.pattern})"
        out.tainted = self.tainted
        return out
    
    def optional(self) -> 'RegularType':
        a = self.nfa
        out = RegularType(automaton=BasicOperations.optional(a))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        if self.pattern is not None:
            out.pattern = f"({self.pattern})?"
        out.tainted = self.tainted
        return out
    
    def kleene_star(self) -> 'RegularType':
        a = self.nfa
        out = RegularType(automaton=BasicOperations.repeat(a, 0))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        if self.pattern is not None:
            out.pattern = f"({self.pattern})*"
        out.tainted = self.tainted
        return out
    
    def kleene_plus(self) -> 'RegularType':
        a = self.nfa
        out = RegularType(automaton=BasicOperations.repeat(a, 1))
        # out.nfa.setDeterministic(False)
        # out.nfa.removeDeadTransitions()
        # out.nfa.minimize()
        if self.pattern is not None:
            out.pattern = f"({self.pattern})+"
        out.tainted = self.tainted
        return out
    

    def reverse(self) -> 'RegularType':
        a = self.nfa
        out_nfa = reverse_automaton(a)
        reverse = RegularType(automaton=out_nfa)
        if self.pattern is not None:
            reverse.pattern = f"({self.pattern})^R"
        reverse.tainted = self.tainted
        return reverse


    def __repr__(self) -> str:
        if self.pattern is None:
            if get_readable_automata_repr_enabled():
                regex = automaton_to_regex(
                    self.nfa,
                    max_states=18,
                    max_transitions=120,
                    max_regex_length=1000,
                    max_edge_length=600,
                    line_based=True,
                )
                if regex is not None:
                    return f"RegularType({regex})"
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
        regex = automaton_to_regex(self.nfa, line_based=True)
        if regex is not None:
            return regex
        return str(self.nfa)

    @property
    def has_start_anchor(self) -> bool:
        if self.ast is None:
            return False
        if isinstance(self.ast, Concatenate):
            if self.ast.nodes and isinstance(self.ast.nodes[0], StartAnchor):
                return True
        return False

    @property
    def has_end_anchor(self) -> bool:
        if self.ast is None:
            return False
        if isinstance(self.ast, Concatenate):
            if self.ast.nodes and isinstance(self.ast.nodes[-1], EndAnchor):
                return True
        return False

    def without_anchors(self) -> 'RegularType':
        if self.ast is None:
            return self
        if not isinstance(self.ast, Concatenate):
            return self
        nodes = list(self.ast.nodes)
        if nodes and isinstance(nodes[0], StartAnchor):
            nodes.pop(0)
        if nodes and isinstance(nodes[-1], EndAnchor):
            nodes.pop()
        if len(nodes) == len(self.ast.nodes):
            return self
        result = RegularType(automaton=self.nfa)
        if not nodes:
            result.ast = Concatenate([])
            result.pattern = ""
        else:
            new_ast = Concatenate(nodes)
            result.ast = new_ast
            result.pattern = ast_to_regex(new_ast)
        result.tainted = self.tainted
        return result

