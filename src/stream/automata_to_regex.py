import functools
from typing import List, Tuple, Dict, Set, Optional
import jpype.imports
if not jpype.isJVMStarted():
    jpype.startJVM(classpath=["jars/automaton.jar"])
from dk.brics.automaton import Automaton, State, RegExp, BasicAutomata # type: ignore

from stream.regex_parser import (
    Node, EmptyLanguageNode, Literal, Dot, CharacterClass, Range, 
    Repeat, Union, Concatenate, ast_to_automaton, ast_to_regex
)

@functools.lru_cache()
def get_singleton(automaton: Automaton) -> Optional[str]:
    s = automaton.getShortestExample(True)
    if s is None:
        return None
    diff = automaton.minus(BasicAutomata.makeString(s))
    if diff.isEmpty():
        return str(s)
    return None

def automaton_to_ast(automaton: Automaton) -> Node:
    """Convert an automaton to a regex AST using state elimination algorithm."""
    converter = AutomatonToRegexConverter()
    return converter.convert(automaton)

class AutomatonToRegexConverter:
    """Converter class for automaton to regex AST conversion using state elimination."""
    
    def _get_state_id(self, state: State, state_to_id: Dict[State, int], prefix: str = "S") -> str:
        if state not in state_to_id:
            state_to_id[state] = len(state_to_id)
        return f"{prefix}{state_to_id[state]}"

    def convert(self, automaton: Automaton) -> Node:
        """Convert an automaton to a regex AST using a full state elimination algorithm."""
        state_to_id_map: Dict[State, int] = {}

        if automaton.isEmpty():
            return EmptyLanguageNode()
        
        if automaton.isEmptyString():
            return Literal("")
        
        nfa = automaton.clone()
        
        q_initial_original = nfa.getInitialState()
        original_accept_states = {s for s in nfa.getStates() if s.isAccept()}

        q_start_processing = State() 
        q_end_processing = State()   

        s_start_proc_id = self._get_state_id(q_start_processing, state_to_id_map, prefix="Q_START_PROC_")
        s_end_proc_id = self._get_state_id(q_end_processing, state_to_id_map, prefix="Q_END_PROC_")
        for s_orig in nfa.getStates():
            self._get_state_id(s_orig, state_to_id_map)

        regex_map: Dict[Tuple[State, State], Node] = {}

        for state_obj in nfa.getStates():
            s_id = self._get_state_id(state_obj, state_to_id_map)
            transitions_by_dest = {}
            for t in state_obj.getTransitions():
                dest = t.getDest()
                if dest not in transitions_by_dest:
                    transitions_by_dest[dest] = []
                transitions_by_dest[dest].append((t.getMin(), t.getMax()))
            
            for dest_obj, char_ranges in transitions_by_dest.items():
                d_id = self._get_state_id(dest_obj, state_to_id_map)
                items: List[Node] = []
                is_dot = False
                for min_char, max_char in char_ranges:
                    if min_char == 0 and max_char == 0xFFFF:
                        is_dot = True; break
                    items.append(Literal(chr(min_char)) if min_char == max_char else Range(chr(min_char), chr(max_char)))
                
                current_regex_node: Optional[Node] = None
                if is_dot: current_regex_node = Dot()
                elif not items: continue
                elif len(items) == 1 and isinstance(items[0], Literal): current_regex_node = items[0]
                else:
                    temp_ranges_for_char_class = []
                    for item_node in items:
                        if isinstance(item_node, Literal):
                            temp_ranges_for_char_class.append((ord(item_node.char), ord(item_node.char)))
                        elif isinstance(item_node, Range):
                            temp_ranges_for_char_class.append((ord(item_node.start), ord(item_node.end)))
                    
                    temp_ranges_for_char_class.sort()
                    total_chars = sum(end - start + 1 for start, end in temp_ranges_for_char_class)
                    
                    if total_chars > (0xFFFF + 1) / 2:
                        complement_ranges = self._compute_complement_ranges(temp_ranges_for_char_class)
                        negated_items_nodes: List[Node] = []
                        for start_val, end_val in complement_ranges:
                            if start_val == end_val:
                                negated_items_nodes.append(Literal(chr(start_val)))
                            else:
                                negated_items_nodes.append(Range(chr(start_val), chr(end_val)))
                        current_regex_node = CharacterClass(True, negated_items_nodes)
                    else:
                        current_regex_node = CharacterClass(False, items)

                if current_regex_node:
                    regex_map[(state_obj, dest_obj)] = current_regex_node

        q_initial_original_id = self._get_state_id(q_initial_original, state_to_id_map)
        regex_map[(q_start_processing, q_initial_original)] = Literal("") 

        if not original_accept_states:
             return EmptyLanguageNode()

        for s_accept in original_accept_states:
            s_accept_id = self._get_state_id(s_accept, state_to_id_map)
            regex_map[(s_accept, q_end_processing)] = Literal("")
        
        states_to_eliminate_now = list(nfa.getStates()) 

        for state_to_elim in states_to_eliminate_now:
            elim_id = self._get_state_id(state_to_elim, state_to_id_map)
            
            self_loop = regex_map.get((state_to_elim, state_to_elim))
            
            incoming_transitions: Dict[State, Node] = {}
            outgoing_transitions: Dict[State, Node] = {}
            
            current_keys = list(regex_map.keys())
            for (src, dst) in current_keys:
                if src == q_end_processing or dst == q_start_processing: continue
                regex_node = regex_map[(src,dst)]
                if dst == state_to_elim and src != state_to_elim:
                    incoming_transitions[src] = regex_node
                elif src == state_to_elim and dst != state_to_elim:
                    outgoing_transitions[dst] = regex_node

            for in_state, in_regex in incoming_transitions.items():
                in_state_id = self._get_state_id(in_state, state_to_id_map)
                for out_state, out_regex in outgoing_transitions.items():
                    out_state_id = self._get_state_id(out_state, state_to_id_map)
                    path_regex: Node
                    if self_loop:
                        loop_star = Repeat(self_loop, 0, None)
                        path_regex = self._make_concatenation(in_regex, loop_star, out_regex)
                    else:
                        path_regex = self._make_concatenation(in_regex, out_regex)
                    
                    key = (in_state, out_state)
                    if key in regex_map:
                        existing_regex = regex_map[key]
                        regex_map[key] = self._make_union([existing_regex, path_regex])
                    else:
                        regex_map[key] = path_regex
            
            keys_to_remove = []
            for key_tuple in list(regex_map.keys()):
                if key_tuple[0] == state_to_elim or key_tuple[1] == state_to_elim:
                    keys_to_remove.append(key_tuple)
            if keys_to_remove:
                for key_to_remove in keys_to_remove:
                    del regex_map[key_to_remove]
        
        final_regex_node = regex_map.get((q_start_processing, q_end_processing))

        if final_regex_node is None:
            if automaton.run(""):
                if automaton.isEmptyString() and not automaton.isEmpty():
                     return Literal("")
            return EmptyLanguageNode() 
            
        return final_regex_node

    def _make_concatenation(self, *args: Node) -> Node:
        nodes = []
        for arg_node in args:
            if isinstance(arg_node, Literal) and arg_node.char == "":
                continue
            elif isinstance(arg_node, Concatenate):
                nodes.extend(arg_node.nodes)
            elif isinstance(arg_node, EmptyLanguageNode):
                return EmptyLanguageNode()
            else:
                nodes.append(arg_node)
        
        if not nodes:
            return Literal("")
        if len(nodes) == 1:
            return nodes[0]
        return Concatenate(nodes)
    
    def _make_union(self, regexes: List[Node]) -> Node:
        raw_items: List[Node] = []
        for regex_node in regexes:
            if isinstance(regex_node, Union):
                raw_items.extend(self._collect_union_items(regex_node))
            elif not isinstance(regex_node, EmptyLanguageNode):
                raw_items.append(regex_node)

        if not raw_items:
            return EmptyLanguageNode()
        if len(raw_items) == 1:
            return raw_items[0]

        unique_str_items: List[Node] = []
        seen_strs: Set[str] = set()
        for item in raw_items:
            item_str = str(item) 
            if item_str not in seen_strs:
                unique_str_items.append(item)
                seen_strs.add(item_str)
        
        if not unique_str_items:
             return EmptyLanguageNode()
        if len(unique_str_items) == 1:
            return unique_str_items[0]

        final_items: List[Node] = []
        for current_node in unique_str_items:
            is_current_subsumed = False
            for i in range(len(final_items) - 1, -1, -1):
                existing_node = final_items[i]
                if self._is_included(current_node, existing_node):
                    is_current_subsumed = True
                    break 
                if self._is_included(existing_node, current_node):
                    final_items.pop(i)
            
            if not is_current_subsumed:
                final_items.append(current_node)

        if not final_items:
            return EmptyLanguageNode()
        if len(final_items) == 1:
            return final_items[0]
        
        return self._build_union_tree(final_items)
    
    def _collect_union_items(self, union_node: Union) -> List[Node]:
        items_collected: List[Node] = []
        
        if isinstance(union_node.left, Union):
            items_collected.extend(self._collect_union_items(union_node.left))
        elif not isinstance(union_node.left, EmptyLanguageNode):
            items_collected.append(union_node.left)
            
        if isinstance(union_node.right, Union):
            items_collected.extend(self._collect_union_items(union_node.right))
        elif not isinstance(union_node.right, EmptyLanguageNode):
            items_collected.append(union_node.right)
        
        return items_collected
    
    def _build_union_tree(self, regexes: List[Node]) -> Node:
        if not regexes: return EmptyLanguageNode()
        if len(regexes) == 1: return regexes[0]
        
        mid = len(regexes) // 2
        if mid == 0:
             return regexes[0]
        
        if len(regexes) == 2:
            return Union(regexes[0], regexes[1])

        return Union(self._build_union_tree(regexes[:mid]), self._build_union_tree(regexes[mid:]))

    def _is_included(self, regex1: Node, regex2: Node) -> bool:
        if regex1 == regex2:
            return True
        
        if isinstance(regex1, EmptyLanguageNode):
            return True
        if isinstance(regex2, EmptyLanguageNode):
            return isinstance(regex1, EmptyLanguageNode)

        try:
            automaton1 = ast_to_automaton(regex1)
            automaton2 = ast_to_automaton(regex2)
            result = automaton1.subsetOf(automaton2)
            return result
        except Exception as e:
            return False
    
    def _compute_complement_ranges(self, ranges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        complement = []
        last_end = -1
        
        for start, end in ranges:
            if start > last_end + 1:
                complement.append((last_end + 1, start - 1))
            
            last_end = max(last_end, end)
        
        if last_end < 0xFFFF:
            complement.append((last_end + 1, 0xFFFF))
            
        return complement 

if __name__ == "__main__":
    automaton = RegExp("~(.*ab.*)").toAutomaton()
    print(automaton)
    ast = automaton_to_ast(automaton)
    print(ast)
    print(ast_to_regex(ast))

    # automaton = RegExp(".*").toAutomaton()
    # print(automaton)
    # ast = automaton_to_ast(automaton)
    # print(ast)
    # print(ast_to_regex(ast))
    # automaton = RegExp("[0-9]+").toAutomaton()
    # print(automaton)
    # ast = automaton_to_ast(automaton)
    # print(ast)
    # print(ast_to_regex(ast))