from collections import deque
import jpype
import jpype.imports

from stream.config.global_config import CONFIG
if not jpype.isJVMStarted():
    jpype.startJVM(classpath=["jars/automaton.jar"])
from dk.brics.automaton import Automaton, RegExp, State, Transition # type: ignore
from stream.tool_error import ToolError

from typing import Deque, List, Callable, Optional, Dict, Set, Tuple
import re

class FST_State:
    def __init__(self, id: int, accept: bool = False) -> None:
        self.id: int = id
        self.accept: bool = accept
        self.transitions: List["FST_Transition"] = []

    def add_transition(self, transition: "FST_Transition") -> None:
        self.transitions.append(transition)

    def __repr__(self) -> str:
        return f"FST_State(id={self.id}, accept={self.accept})\n" + "\n".join(f"  {t}" for t in self.transitions) + "\n"

class FST_Transition:
    def __init__(self, min: Optional[str], max: Optional[str], output: str, to: FST_State, is_other: bool = False, is_not_consumed = False, is_epsilon: bool = False) -> None:
        self.min: Optional[str] = min
        self.max: Optional[str] = max
        self.output: str = output
        self.to: FST_State = to
        self.is_other: bool = is_other
        self.is_not_consumed: bool = is_not_consumed
        self.is_epsilon: bool = is_epsilon

    def applies(self, c: str) -> bool:
        # Epsilon transition: min=None, max=None, is_epsilon=True
        # Can accept any character but doesn't consume it
        if self.min is None and self.max is None and self.is_epsilon:
            return True
        if self.min is None or self.max is None:
            return False
        return ord(self.min) <= ord(c) <= ord(self.max)

    def transform(self, c: str) -> str:
        if self.output == "$self":
            return c
        elif "$self" in self.output:
            return self.output.replace("$self", c)
        elif "--" in self.output:
            parts = self.output.split("--")
            if len(parts) != 2:
                raise ToolError(f"Invalid transition output: {self.output}")
            min_out, max_out = parts[0], parts[1]
            if ord(min_out) > ord(max_out):
                raise ToolError(f"Invalid transition output: {self.output}")
            return chr(min(ord(min_out) + ord(c) - ord(self.min), ord(max_out)))
        else:
            return self.output
    
    def __repr__(self) -> str:
        min_out = self.transform(self.min)
        max_out = self.transform(self.max)
        if len(min_out) == 1 and len(max_out) == 1:
            return f"FST_Transition(min={ord(self.min)}, max={ord(self.max)}, min_out={ord(min_out)}, max_out={ord(max_out)}, to={self.to.id})"
        elif min_out == max_out:
            return f"FST_Transition(min={ord(self.min)}, max={ord(self.max)}, out='{min_out}', to={self.to.id})"
        elif isinstance(self.output, str):
            if self.output.endswith("$self"):
                return f"FST_Transition(min={ord(self.min)}, max={ord(self.max)}, min_out='{self.output[:-5]}'{ord(self.min)}, max_out='{self.output[:-5]}'{ord(self.max)}, to={self.to.id})"
        return f"FST_Transition(min={ord(self.min)}, max={ord(self.max)}, out='{min_out}--{max_out}', to={self.to.id})"

class FST:
    def __init__(self) -> None:
        self.states: Dict[int, FST_State] = {}
        self.initial: Optional[FST_State] = None

    def add_state(self, state_id: int, accept: bool = False) -> FST_State:
        if state_id not in self.states:
            self.states[state_id] = FST_State(state_id, accept)
        else:
            if accept:
                self.states[state_id].accept = True
        return self.states[state_id]

    def set_start(self, state_id: int) -> None:
        self.initial = self.add_state(state_id)

    def set_accept(self, state_id: int) -> None:
        state = self.add_state(state_id, accept=True)
        state.accept = True

    def add_transition(self, from_state_id: int, min_in: str, max_in: Optional[str], output: str, next_state_id: int, is_not_consumed = False, is_epsilon: bool = False) -> None:
        from_state = self.add_state(from_state_id)
        next_state = self.add_state(next_state_id)
        is_other = False
        # is_other_not_consume = False
        if min_in == "$epsilon":
            is_epsilon = True
            start_val, end_val = None, None
        elif min_in == "$other":
            is_other = True
            start_val, end_val = None, None
        elif min_in == "$all":
            start_val, end_val = chr(0), chr(65535)
        # elif min_in == "$other_not_consume":
        #     is_other_not_consume = True
        #     start_val, end_val = None, None
        else:
            start_val, end_val = min_in, max_in
        trans = FST_Transition(start_val, end_val, output, to=next_state, is_other=is_other, is_not_consumed=is_not_consumed, is_epsilon=is_epsilon)
        from_state.add_transition(trans)

    def _merge_intervals(self, intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        if not intervals:
            return []
        intervals.sort(key=lambda x: x[0])
        merged: List[Tuple[int, int]] = []
        current_min, current_max = intervals[0]
        for s, e in intervals[1:]:
            if s <= current_max + 1:
                current_max = max(current_max, e)
            else:
                merged.append((current_min, current_max))
                current_min, current_max = s, e
        merged.append((current_min, current_max))
        return merged

    def _compute_complement_intervals(self, intervals: List[Tuple[int, int]], min_val: int = 0, max_val: int = 65535) -> List[Tuple[int, int]]:
        complement: List[Tuple[int, int]] = []
        current = min_val
        for s, e in intervals:
            if current < s:
                complement.append((current, s - 1))
            current = max(current, e + 1)
        if current <= max_val:
            complement.append((current, max_val))
        return complement

    def _process_other_transitions(self) -> None:
        for state in self.states.values():
            other_transitions: List[FST_Transition] = [t for t in state.transitions if t.is_other]
            if not other_transitions:
                continue
            explicit_intervals: List[Tuple[int, int]] = []
            for t in state.transitions:
                if not t.is_other and t.min is not None and t.max is not None:
                    explicit_intervals.append((ord(t.min), ord(t.max)))
            merged = self._merge_intervals(explicit_intervals)
            complement = self._compute_complement_intervals(merged)
            for other in other_transitions:
                for comp_min, comp_max in complement:
                    new_min = chr(comp_min)
                    new_max = chr(comp_max)
                    new_trans = FST_Transition(new_min, new_max, other.output, to=other.to, is_other=False, is_not_consumed=other.is_not_consumed)
                    state.add_transition(new_trans)
            state.transitions = [t for t in state.transitions if not t.is_other]

    def _process_not_consumed_transitions(self) -> None:
        for state in self.states.values():
            not_consumed_transtion: List[FST_Transition] = [t for t in state.transitions if t.is_not_consumed]
            if not not_consumed_transtion:
                continue
            for t in not_consumed_transtion:
                # Check if target state has not_consumed or epsilon transitions
                target_state = t.to
                has_not_consumed = any(trans.is_not_consumed for trans in target_state.transitions)
                has_epsilon = any(trans.is_epsilon for trans in target_state.transitions)
                
                if has_not_consumed or has_epsilon:
                    raise ToolError(f"Cannot eliminate not_consumed transition: target state {target_state.id} has not_consumed or epsilon transitions")
                
                for des_transition in t.to.transitions:
                    if ord(t.max) >= ord(des_transition.min) and ord(t.min) <= ord(des_transition.max):
                        new_min = t.min if ord(t.min) > ord(des_transition.min) else des_transition.min
                        new_max = t.max if ord(t.max) < ord(des_transition.max) else des_transition.max
                        new_trans = FST_Transition(new_min, new_max, t.output + des_transition.output, to=des_transition.to)
                        state.add_transition(new_trans)
            state.transitions = [t for t in state.transitions if not t.is_not_consumed]

    def transform_all(self, input_string: str) -> Set[str]:
        if self.initial is None:
            return set()
        
        def epsilon_closure(configurations: Set[Tuple[FST_State, str]]) -> Set[Tuple[FST_State, str]]:
            """Compute epsilon closure of the given configurations"""
            closure = set(configurations)
            changed = True
            while changed:
                changed = False
                new_configs = set()
                for state, output_so_far in closure:
                    for trans in state.transitions:
                        if trans.is_epsilon:
                            new_state = trans.to
                            new_output = output_so_far + trans.output
                            new_config = (new_state, new_output)
                            if new_config not in closure:
                                new_configs.add(new_config)
                                changed = True
                closure.update(new_configs)
            return closure
        
        configurations: Set[Tuple[FST_State, str]] = epsilon_closure({(self.initial, "")})
        
        for c in input_string:
            next_configurations: Set[Tuple[FST_State, str]] = set()
            for state, output_so_far in configurations:
                for trans in state.transitions:
                    if not trans.is_epsilon and trans.applies(c):
                        new_state = trans.to
                        new_output = output_so_far + trans.transform(c)
                        next_configurations.add((new_state, new_output))
            configurations = epsilon_closure(next_configurations)
        
        results: Set[str] = {out for state, out in configurations if state.accept}
        return results
    
    def output_projection(self) -> Automaton:
        """Compute the output projection of this FST to get an Automaton"""
        result = Automaton()
        state_mapping: Dict[FST_State, State] = {}
        
        # Create initial state
        if self.initial is not None:
            state_mapping[self.initial] = result.getInitialState()
            state_mapping[self.initial].setAccept(self.initial.accept)
        
        # Process all states and transitions
        empty_transitions: Set[Tuple[State, State]] = set()
        
        for fst_state in self.states.values():
            if fst_state not in state_mapping:
                state_mapping[fst_state] = State()
                state_mapping[fst_state].setAccept(fst_state.accept)
            
            current_state = state_mapping[fst_state]
            
            for trans in fst_state.transitions:
                if trans.to not in state_mapping:
                    state_mapping[trans.to] = State()
                    state_mapping[trans.to].setAccept(trans.to.accept)
                
                target_state = state_mapping[trans.to]
                
                # Handle epsilon transitions
                if trans.is_epsilon:
                    if trans.output:
                        # Create transitions for the output string
                        temp_state = current_state
                        for i, c in enumerate(trans.output):
                            if i == len(trans.output) - 1:
                                temp_state.addTransition(Transition(c, c, target_state))
                            else:
                                next_state = State()
                                temp_state.addTransition(Transition(c, c, next_state))
                                temp_state = next_state
                    else:
                        # Empty output - add to empty transitions
                        empty_transitions.add((current_state, target_state))
                    continue
                
                # Handle output for regular transitions
                if trans.min is None or trans.max is None:
                    continue
                    
                min_out = trans.transform(trans.min)
                max_out = trans.transform(trans.max)
                
                if len(min_out) == 0 or len(max_out) == 0:
                    if min_out != max_out:
                        raise ToolError(f"Output range not supported: {min_out}--{max_out}")
                    empty_transitions.add((current_state, target_state))
                elif len(min_out) > 1 or len(max_out) > 1:
                    if "$self" in trans.output:
                        if not trans.output.endswith("$self") and not trans.output.startswith("$self"):
                            raise ToolError(f"Output range not supported: {min_out}--{max_out}")
                        if trans.output.endswith("$self"):
                            prefix = trans.output[:-5]
                            if prefix:
                                temp_state = current_state
                                for i, c in enumerate(prefix):
                                    next_state = State()
                                    temp_state.addTransition(Transition(c, c, next_state))
                                    temp_state = next_state
                                temp_state.addTransition(Transition(min_out[-1], max_out[-1], target_state))
                            else:
                                current_state.addTransition(Transition(min_out, max_out, target_state))
                        elif trans.output.startswith("$self"):
                            suffix = trans.output[5:]
                            if suffix:
                                temp_state = State()
                                current_state.addTransition(Transition(min_out[0], max_out[0], temp_state))
                                for i, c in enumerate(suffix):
                                    if i != len(suffix) - 1:
                                        next_state = State()
                                        temp_state.addTransition(Transition(c, c, next_state))
                                        temp_state = next_state
                                    else:
                                        temp_state.addTransition(Transition(c, c, target_state))
                            else:
                                current_state.addTransition(Transition(min_out, max_out, target_state))
                    else:
                        temp_state = current_state
                        for i, c in enumerate(min_out):
                            if i != len(min_out) - 1:
                                next_state = State()
                                temp_state.addTransition(Transition(c, c, next_state))
                                temp_state = next_state
                            else:
                                temp_state.addTransition(Transition(c, c, target_state))
                else:
                    current_state.addTransition(Transition(min_out, max_out, target_state))
        
        process_empty_transitions(empty_transitions)
        result.setDeterministic(False)
        result.removeDeadTransitions()
        result.minimize()
        return result

    def __repr__(self) -> str:
        sorted_states = sorted(self.states.items(), key=lambda x: x[0])
        return f"Initial: {self.initial.id}\n" + "\n".join(f"{state_id}: {state}" for state_id, state in sorted_states)

def create_fst(transition_specs: List[Tuple[int, str, str, int] | Tuple[int, str, str, int, bool]], start_state: int = 0, final_states: Optional[Set[int]] = None) -> FST:
    fst = FST()
    fst.set_start(start_state)
    if final_states is None:
        final_states = {start_state}
    for spec in transition_specs:
        if len(spec) == 5:
            from_state, input_range, output, next_state, is_not_consumed = spec
        else:
            from_state, input_range, output, next_state = spec
            is_not_consumed = False
        
        if input_range == "$epsilon":
            fst.add_transition(from_state, "$epsilon", None, output, next_state, is_not_consumed=False, is_epsilon=True)
        elif input_range == "$other":
            fst.add_transition(from_state, "$other", None, output, next_state, is_not_consumed, is_epsilon = False)
        # elif input_range == "$other_not_consume":
        #     fst.add_transition(from_state, "$other_not_consume", None, output, next_state)
        else:
            if '--' in input_range:
                if "---" in input_range:
                    if input_range.startswith("---"):
                        min_in = "-"
                        max_in = input_range[3:]
                    elif input_range.endswith("---"):
                        min_in = input_range[:-3]
                        max_in = "-"
                    else:
                        raise ToolError(f"Invalid input range format: {input_range}")
                else:
                    parts = input_range.split('--')
                    if len(parts) != 2:
                        raise ToolError(f"Invalid input range format: {input_range}")
                    min_in, max_in = parts[0], parts[1]
            else:
                min_in = input_range
                max_in = input_range
            fst.add_transition(from_state, min_in, max_in, output, next_state, is_not_consumed, is_epsilon = False)
    for fs in final_states:
        fst.set_accept(fs)
    fst._process_other_transitions()
    fst._process_not_consumed_transitions()
    return fst

def line_based_functional_to_stream_FST(fst: FST) -> FST:
    start_state_id = fst.initial.id
    for state in fst.states.values():
        new_transitions: List[FST_Transition] = []
        for transition in state.transitions:
            min_char = transition.min
            max_char = transition.max
            if min_char == None:
                if max_char != "\n":
                    new_transitions.append(transition)
                continue
            if max_char == None:
                if min_char != "\n":
                    new_transitions.append(transition)
                continue
            if ord(min_char) > ord("\n") or ord(max_char) < ord("\n"):
                new_transitions.append(transition)
                continue
            if ord(min_char) == ord("\n") and ord(max_char) == ord("\n"):
                continue
            m = chr(ord("\n") - 1)
            n = chr(ord("\n") + 1)
            if ord(min_char) == ord("\n"):
                new_transitions.append(FST_Transition(n, max_char, transition.output, transition.to, transition.is_other, transition.is_not_consumed))
                continue
            if ord(max_char) == ord("\n"):
                new_transitions.append(FST_Transition(min_char, m, transition.output, transition.to, transition.is_other, transition.is_not_consumed))
                continue
            new_transitions.append(FST_Transition(min_char, m, transition.output, transition.to, transition.is_other, transition.is_not_consumed))
            new_transitions.append(FST_Transition(n, max_char, transition.output, transition.to, transition.is_other, transition.is_not_consumed))
        state.transitions = new_transitions
        if state.accept:
            fst.add_transition(state.id, "\n", "\n", "\n", start_state_id)
    return fst

def product_fst_automaton_with_projection(fst: FST, automaton: Automaton) -> Automaton:
    if not CONFIG.get("enable_FST", True):
        return RegExp(".*").toAutomaton()
    
    # First, compute the complete FST (FST x NFA = FST)
    product_fst = FST()
    worklist: Deque[Tuple[FST_State, State]] = deque()
    state_to_id: Dict[State, int] = {}  # Map automaton states to unique IDs
    state_mapping: Dict[Tuple[int, int], int] = {}  # (fst_state_id, automaton_state_id) -> product_state_id
    state_counter = 0
    auto_state_counter = 0
    
    # Assign unique ID to initial automaton state
    initial_auto_state = automaton.getInitialState()
    state_to_id[initial_auto_state] = auto_state_counter
    auto_state_counter += 1
    
    # Create initial state
    initial_pair = (fst.initial.id, state_to_id[initial_auto_state])
    state_mapping[initial_pair] = state_counter
    product_fst.set_start(state_counter)
    state_counter += 1
    
    worklist.append((fst.initial, initial_auto_state))
    
    while worklist:
        fst_state, auto_state = worklist.popleft()
        
        # Ensure automaton state has an ID
        if auto_state not in state_to_id:
            state_to_id[auto_state] = auto_state_counter
            auto_state_counter += 1
        
        current_state_id = state_mapping[(fst_state.id, state_to_id[auto_state])]
        
        # Set accept state if both are accepting
        if fst_state.accept and auto_state.isAccept():
            product_fst.set_accept(current_state_id)
        
        # Compute product transitions
        for fst_trans in fst_state.transitions:
            # Handle epsilon transitions (don't consume input)
            if fst_trans.is_epsilon:
                # Epsilon transitions don't require input overlap with automaton
                # The automaton state stays the same, only FST state changes
                if fst_trans.to.id not in state_to_id:
                    state_to_id[auto_state] = auto_state_counter if auto_state not in state_to_id else state_to_id[auto_state]
                
                target_pair = (fst_trans.to.id, state_to_id[auto_state])
                if target_pair not in state_mapping:
                    state_mapping[target_pair] = state_counter
                    state_counter += 1
                    worklist.append((fst_trans.to, auto_state))
                
                target_state_id = state_mapping[target_pair]
                
                # Add epsilon transition to product FST
                product_fst.add_transition(
                    current_state_id,
                    "$epsilon",
                    None,
                    fst_trans.output,
                    target_state_id,
                    fst_trans.is_not_consumed,
                    is_epsilon=True
                )
            else:
                # Handle regular transitions
                for auto_trans in auto_state.getSortedTransitions(True):
                    # Check if input ranges overlap
                    if (fst_trans.min is not None and fst_trans.max is not None and
                        ord(auto_trans.getMax()) >= ord(fst_trans.min) and 
                        ord(auto_trans.getMin()) <= ord(fst_trans.max)):
                        
                        # Compute intersection of input ranges
                        min_in = fst_trans.min if ord(fst_trans.min) > ord(auto_trans.getMin()) else auto_trans.getMin()
                        max_in = fst_trans.max if ord(fst_trans.max) < ord(auto_trans.getMax()) else auto_trans.getMax()
                        
                        # Ensure target automaton state has an ID
                        target_auto_state = auto_trans.getDest()
                        if target_auto_state not in state_to_id:
                            state_to_id[target_auto_state] = auto_state_counter
                            auto_state_counter += 1
                        
                        # Create target state if not exists
                        target_pair = (fst_trans.to.id, state_to_id[target_auto_state])
                        if target_pair not in state_mapping:
                            state_mapping[target_pair] = state_counter
                            state_counter += 1
                            worklist.append((fst_trans.to, target_auto_state))
                        
                        target_state_id = state_mapping[target_pair]
                        
                        # Add transition to product FST
                        # Input is the intersection range, output is the FST's output
                        product_fst.add_transition(
                            current_state_id, 
                            min_in, 
                            max_in, 
                            fst_trans.output, 
                            target_state_id,
                            fst_trans.is_not_consumed
                        )
    
    # Process the FST to handle special transitions
    product_fst._process_other_transitions()
    product_fst._process_not_consumed_transitions()
    
    # compute the output projection
    return product_fst.output_projection()




def product_fst_automaton(fst: FST, automaton: Automaton) -> Automaton:
    if not CONFIG.get("enable_FST", True):
        return RegExp(".*").toAutomaton()
    product = Automaton()
    worklist: Deque[Tuple[State, FST_State, State]] = deque()
    new_states: Dict[Tuple[State, FST_State], State] = {}
    p = (fst.initial, automaton.getInitialState())
    worklist.append(p)
    new_states[p] = product.getInitialState()
    empty_transitions: Set[Tuple[State, State]] = set()
    while worklist:
        p = worklist.popleft()
        s_product = new_states[p]
        s_fst, s_automaton = p
        s_product.setAccept(s_fst.accept and s_automaton.isAccept())
        transitions_fst = fst.states[s_fst.id].transitions
        transitions_automaton = s_automaton.getSortedTransitions(True)
        for t_fst in transitions_fst:
            # Handle epsilon transitions (don't consume input)
            if t_fst.is_epsilon:
                # Epsilon transitions don't require input overlap with automaton
                # The automaton state stays the same, only FST state changes
                p_epsilon = (t_fst.to, s_automaton)
                if p_epsilon not in new_states:
                    s_epsilon = State()
                    new_states[p_epsilon] = s_epsilon
                    worklist.append(p_epsilon)
                s_epsilon = new_states[p_epsilon]
                
                # Add epsilon transition (empty output)
                if t_fst.output:
                    # Create transitions for the output string
                    current_state = s_product
                    for i, c in enumerate(t_fst.output):
                        if i == len(t_fst.output) - 1:
                            current_state.addTransition(Transition(c, c, s_epsilon))
                        else:
                            next_state = State()
                            current_state.addTransition(Transition(c, c, next_state))
                            current_state = next_state
                else:
                    empty_transitions.add((s_product, s_epsilon))
            else:
                # Handle regular transitions
                for t_automaton in transitions_automaton:
                    if ord(t_automaton.getMax()) >= ord(t_fst.min) and ord(t_automaton.getMin()) <= ord(t_fst.max):
                        p = (t_fst.to, t_automaton.getDest())
                        if p not in new_states:
                            s = State()
                            new_states[p] = s
                            worklist.append(p)
                        s = new_states[p]
                        min_in = t_fst.min if ord(t_fst.min) > ord(t_automaton.getMin()) else t_automaton.getMin()
                        max_in = t_fst.max if ord(t_fst.max) < ord(t_automaton.getMax()) else t_automaton.getMax()
                        min_out = t_fst.transform(min_in)
                        max_out = t_fst.transform(max_in)
                        if len(min_out) == 0 or len(max_out) == 0:
                            if min_out != max_out:
                                raise ToolError(f"Output range not supported: {min_out}--{max_out}")
                            empty_transitions.add((s_product, s))
                        elif len(min_out) > 1 or len(max_out) > 1:
                            # if min_out != max_out:
                            #     raise ToolError(f"Output range not supported: {min_out}--{max_out}")
                            if "$self" in t_fst.output:
                                if not t_fst.output.endswith("$self") and not t_fst.output.startswith("$self"):
                                    raise ToolError(f"Output range not supported: {min_out}--{max_out}")
                                if t_fst.output.endswith("$self"):
                                    min_out = t_fst.output[:-5]
                                    max_out = t_fst.output[:-5]
                                    if min_out != max_out:
                                        raise ToolError(f"Output range not supported: {min_out}--{max_out}")
                                    current_state = s_product
                                    for i, c in enumerate(min_out):
                                        s_1 = State()
                                        current_state.addTransition(Transition(c, c, s_1))
                                        current_state = s_1
                                    current_state.addTransition(Transition(min_in, max_in, s))
                                if t_fst.output.startswith("$self"):
                                    min_out = t_fst.output[5:]
                                    max_out = t_fst.output[5:]
                                    if min_out != max_out:
                                        raise ToolError(f"Output range not supported: {min_out}--{max_out}")
                                    current_state = State()
                                    s_product.addTransition(Transition(min_in, max_in, current_state))
                                    for i, c in enumerate(min_out):
                                        if i != len(min_out) - 1:
                                            s_1 = State()
                                            current_state.addTransition(Transition(c, c, s_1))
                                            current_state = s_1
                                        else:
                                            current_state.addTransition(Transition(c, c, s))
                            else:
                                current_state = s_product
                                for i, c in enumerate(min_out):
                                    if i != len(min_out) - 1:
                                        s_1 = State()
                                        current_state.addTransition(Transition(c, c, s_1))
                                        current_state = s_1
                                    else:
                                        current_state.addTransition(Transition(c, c, s))
                        else:
                            s_product.addTransition(Transition(min_out, max_out, s))

    process_empty_transitions(empty_transitions)
    product.setDeterministic(False)
    product.removeDeadTransitions()
    product.minimize()
    return product

def process_empty_transitions(empty_transitions: Set[Tuple[State, State]]) -> None:
    empty_closure = {}
    for src, dst in empty_transitions:
        if src not in empty_closure:
            empty_closure[src] = set()
        empty_closure[src].add(dst)
    
    # compute transitive closure
    changed = True
    while changed:
        changed = False
        for src, dsts in list(empty_closure.items()):
            old_size = len(dsts)
            new_dsts = set()
            for dst in dsts:
                if dst in empty_closure:
                    new_dsts.update(empty_closure[dst])
            if new_dsts:
                dsts.update(new_dsts)
                if len(dsts) > old_size:
                    changed = True
    
    for src, dsts in empty_closure.items():
        if any(dst.isAccept() for dst in dsts):
            src.setAccept(True)
        
        for dst in dsts:
            for trans in dst.getTransitions():
                src.addTransition(Transition(trans.getMin(), trans.getMax(), trans.getDest()))

def full_stream_to_line_based_FST() -> FST:
    specs = [
        (-1, "\n", "", 100),
        (-1, "\n", "", 0),
        (-1, "$other", "$self", 1),
        (-1, "$other", "", 2),
        (0, "\n", "", 100),
        (0, "\n", "", 0),
        (0, "$other", "$self", 1),
        (0, "$other", "", 2),
        (1, "\n", "", 100),
        (1, "$other", "$self", 1),
        (2, "\n", "", 0),
        (2, "$other", "", 2),
        (100, "$other", "", 100),
    ]
    # return create_fst(specs, start_state=-1, final_states={-1, 1, 100})
    return create_fst(specs, start_state=-1, final_states={1, 100})

def translate_to_line_delimited_FST(set1: str) -> FST:
    specs = []
    for c in set1:
        specs.append((0, c, "", 0))
        specs.append((0, c, "", 100))
        specs.append((1, c, "", 100))
        specs.append((2, c, "", 0))
        specs.append((2, c, "", 3))
    specs.extend([
        (0, "$other", "$self", 1),
        (0, "$other", "", 2),
        (1, "$other", "$self", 1),
        (2, "$other", "", 2),
        (100, "$other", "", 100),
    ])
    return create_fst(specs, start_state=0, final_states={1, 3, 100})


def translation_FST(set1: str, set2: str) -> FST:
    specs = []
    for i, c in enumerate(set1):
        if i < len(set2):
            c2 = set2[i]
        else:
            c2 = set2[-1]
        specs.append((0, c, c2, 0))
    specs.append((0, "$other", "$self", 0))
    return create_fst(specs, start_state=0, final_states={0})


def compression_FST(set1: str) -> FST:
    specs = []
    mapping: Dict[str, int] = {}
    final_states: Set[int] = {0}
    for i, c in enumerate(set1):
        mapping[c] = i + 1
        final_states.add(i + 1)
    for c, i in mapping.items():
        specs.append((0, c, c, i))
        specs.append((i, c, "", i))
        for c2, i2 in mapping.items():
            if i2 == i:
                continue
            specs.append((i, c2, c2, i2))
        specs.append((i, "$other", "$self", 0))
    specs.append((0, "$other", "$self", 0))
    return create_fst(specs, start_state=0, final_states=final_states)


def deletion_FST(set1: str) -> FST:
    specs = []
    for c in set1:
        specs.append((0, c, "", 0))
    specs.append((0, "$other", "$self", 0))
    return create_fst(specs, start_state=0, final_states={0})

def cut_field_FST(delimiter: str, fields: List[int], has_upperbound: bool = True) -> FST:
    # cut -f 1 -> [1]
    # cut -f 1,3 -> [1, 3]
    # cut -f 1-3 -> [1, 2, 3]
    # cut -f 1- -> [1], no upperbound
    specs = []
    max_field = max(fields)
    for i in range(1, max_field + 1):
        if i in fields and (i != max_field or not has_upperbound):
            specs.append((i, delimiter, delimiter, i + 1))
        else:
            specs.append((i, delimiter, "", i + 1))
        
        if i in fields:
            specs.append((i, "$other", "$self", i))
        else:
            specs.append((i, "$other", "", i))
    if has_upperbound:
        specs.append((max_field + 1, "$other", "", max_field + 1))
    else:
        specs.append((max_field + 1, "$other", "$self", max_field + 1))
    return create_fst(specs, start_state=1, final_states={i for i in range(1, max_field + 2)})


def correct_cut_field_FST(delimiter: str, fields: List[int], has_upperbound: bool = True, cut_stream: bool = False) -> FST:
    if delimiter == "\n" and not cut_stream:
        raise ToolError("cut: invalid field specification")
    if delimiter != "\n" and cut_stream:
        raise ValueError("cut: invalid field specification")
    specs = []
    max_field = max(fields)
    for i in range(1, max_field + 1):
        if i in fields and (i != max_field or not has_upperbound):
            specs.append((i, delimiter, delimiter, i + 1))
        else:
            specs.append((i, delimiter, "", i + 1))
        
        if i in fields:
            specs.append((i, "$other", "$self", i))
        else:
            specs.append((i, "$other", "", i))
    if has_upperbound:
        specs.append((max_field + 1, "$other", "", max_field + 1))
    else:
        specs.append((max_field + 1, "$other", "$self", max_field + 1))

    if 1 in fields and (i != max_field or not has_upperbound):
        specs.append((0, delimiter, delimiter, 2))
    else:
        specs.append((0, delimiter, "", 2))
    if 1 in fields:
        specs.append((0, "$other", "$self", 1))
    else:
        specs.append((0, "$other", "", 1))
    specs.append((0, "$other", "$self", -1))
    specs.append((-1, delimiter, "", -2))
    specs.append((-1, "$other", "$self", -1))
    return create_fst(specs, start_state=0, final_states={i for i in range(2, max_field + 2)} | {0, -1})

def tail_FST(delimiter: str, n: int) -> FST:
    specs = []
    specs.append((0, delimiter, "", 0))
    specs.append((0, delimiter, "", 1))
    specs.append((0, "$other", "", 0))
    specs.append((-1, delimiter, "", 0))
    specs.append((-1, delimiter, "", 1))
    specs.append((-1, "$other", "", 0))
    for i in range(1, n):
        specs.append((i, delimiter, "$self", i + 1))
        specs.append((i, "$other", "$self", i))
        specs.append((-1, delimiter, "$self", i + 1))
        specs.append((-1, "$other", "$self", i))
    specs.append((n, delimiter, "$self", n + 1))
    specs.append((-1, delimiter, "$self", n + 1))
    specs.append((n, "$other", "$self", n + 2))
    specs.append((-1, "$other", "$self", n + 2))
    specs.append((n + 2, delimiter, "$self", n + 1))
    specs.append((n + 2, "$other", "$self", n + 2))
    return create_fst(specs, start_state=-1, final_states={-1, n + 1, n + 2})

def head_FST(delimiter: str, n: int) -> FST:
    specs = []
    for i in range(0, n):
        specs.append((i, delimiter, "$self", i + 1))
        specs.append((i, "$other", "$self", i))
    specs.append((n, "$other", "", n))
    return create_fst(specs, start_state=0, final_states={i for i in range(0, n + 1)})


def add_newline_if_not_end_with_newline_FST() -> FST:
    specs = [
        (0, "\n", "$self", 1),
        (0, "$other", "$self", 0),
        (0, "$other", "$self" + "\n", 2),
        (1, "\n", "$self", 1),
        (1, "$other", "$self", 0),
        (1, "$other", "$self" + "\n", 2),
    ]
    return create_fst(specs, start_state=0, final_states={1, 2})
    
        

# def cut_field_no_upperbound_FST(delimiter: str, start_field: int, leading_delimiter : bool = False) -> FST:
#     specs = []
#     for i in range(1, start_field):
#         if i == start_field - 1 and leading_delimiter:
#             specs.append((i, delimiter, "$self", i + 1))
#         else:
#             specs.append((i, delimiter, "", i + 1))
#         specs.append((i, "$other", "", i))

#     specs.append((start_field, "$other", "$self", start_field))
#     return create_fst(specs, start_state=1, final_states={i for i in range(1, start_field + 1)})

def cut_char_FST(fields: List[int], has_upperbound: bool = True) -> FST:
    specs = []
    max_field = max(fields)
    for i in range(1, max_field + 1):
        if i in fields:
            specs.append((i, "$other", "$self", i + 1))
        else:
            specs.append((i, "$other", "", i + 1))
    if has_upperbound:
        specs.append((max_field + 1, "$other", "", max_field + 1))
    else:
        specs.append((max_field + 1, "$other", "$self", max_field + 1))
    return create_fst(specs, start_state=1, final_states={i for i in range(1, max_field + 2)})



def filter_FST(automaton: Automaton) -> FST:
    automaton.determinize()
    automaton.minimize()
    automaton.removeDeadTransitions()
    state_map: Dict[State, int] = {}
    specs = []
    states = automaton.getStates()
    for i, state in enumerate(states):
        state_map[state] = i + 1
    initial_state_id = state_map[automaton.getInitialState()]
    final_states = set()
    for state in states:
        state_id = state_map[state]
        if state.isAccept():
            final_states.add(state_id)
        for trans in state.getSortedTransitions(True):
            min_char = trans.getMin()
            max_char = trans.getMax()
            input_range = min_char + "--" + max_char
            dest_state_id = state_map[trans.getDest()]
            specs.append((state_id, input_range, "$self", dest_state_id))
    return create_fst(specs, start_state=initial_state_id, final_states=final_states)


def stream_based_filter_FST(automaton: Automaton) -> FST:
    automaton.determinize()
    automaton.minimize()
    automaton.removeDeadTransitions()
    state_map: Dict[State, int] = {}
    specs = []
    states = automaton.getStates()
    for i, state in enumerate(states):
        state_map[state] = i + 1
    initial_state = automaton.getInitialState()
    final_states = set()
    garbage_state_id = -max(state_map.values()) - 1
    fallback_state_id = -garbage_state_id
    for state in states:
        state_id = state_map[state]
        if state.isAccept():
            final_states.add(state_id)
            specs.append((state_id, "\n", "\n", 0))
            specs.append((-state_id, "\n", "", garbage_state_id))
        else:
            final_states.add(-state_id)
            specs.append((-state_id, "\n", "", 0))
        trans_specs = []
        for trans in state.getSortedTransitions(True):
            min_char = trans.getMin()
            max_char = trans.getMax()
            dest_state_id = state_map[trans.getDest()]

            m = chr(ord("\n") - 1)
            n = chr(ord("\n") + 1)
            if ord(min_char) == ord("\n") and ord(max_char) == ord("\n"):
                continue
            if ord(min_char) == ord("\n"):
                trans_specs.append((state_id, n + "--" + max_char, "$self", dest_state_id))
                trans_specs.append((-state_id, n + "--" + max_char, "", -dest_state_id))
                continue
            if ord(max_char) == ord("\n"):
                trans_specs.append((state_id, min_char + "--" + m, "$self", dest_state_id))
                trans_specs.append((-state_id, min_char + "--" + m, "", -dest_state_id))
                continue
            if ord(min_char) <= ord("\n") and ord(max_char) >= ord("\n"):
                trans_specs.append((state_id, min_char + "--" + m, "$self", dest_state_id))
                trans_specs.append((state_id, n + "--" + max_char, "$self", dest_state_id))
                trans_specs.append((-state_id, n + "--" + max_char, "", -dest_state_id))
                trans_specs.append((-state_id, min_char + "--" + m, "", -dest_state_id))
                continue
            trans_specs.append((state_id, min_char + "--" + max_char, "$self", dest_state_id))
            trans_specs.append((-state_id, min_char + "--" + max_char, "", -dest_state_id))
        specs.extend(trans_specs)
        # specs.append((state_id, "$other", "$self", garbage_state_id))
        specs.append((-state_id, "$other", "", fallback_state_id))
        if state == initial_state:
            for trans_spec in trans_specs:
                specs.append((0, trans_spec[1], trans_spec[2], trans_spec[3]))
    if initial_state.isAccept():
        specs.append((0, "\n", "\n", 0))
    else:
        specs.append((0, "\n", "", 0))
    specs.append((0, "$other", "", fallback_state_id))
    specs.append((fallback_state_id, "\n", "", 0))
    specs.append((fallback_state_id, "$other", "", fallback_state_id))
    return create_fst(specs, start_state=0, final_states=final_states | {0, fallback_state_id})
    
    
            

# def cut_char_no_upperbound_FST(start_field: int) -> FST:
#     specs = []
#     for i in range(1, start_field):
#         specs.append((i, "$other", "", i + 1))
#     specs.append((start_field, "$other", "$self", start_field))
#     return create_fst(specs, start_state=1, final_states={i for i in range(1, start_field + 1)})

# TODO
# def add_newline_if_not_end_with_newline() -> FST:
#     specs = [

#     ]

def global_replacement_FST(s1: str, s2: str) -> FST:
    m = len(s1)
    if m == 0:
        raise ValueError("s1 must be nonempty")
    
    # Compute the KMP failure function for s1.
    failure = [0] * m
    for i in range(1, m):
        j = failure[i - 1]
        while j > 0 and s1[i] != s1[j]:
            j = failure[j - 1]
        if s1[i] == s1[j]:
            j += 1
        failure[i] = j

    delta_memo = {}
    
    def delta(i, a) -> Optional[Tuple[int, str]]:
        key = (i, a)
        if key in delta_memo:
            return delta_memo[key]
            
        result = None
        if a == s1[i]:
            if i == m - 1:
                # Full match: output s2 and fall back.
                result = (0, s2)
            else:
                result = (i + 1, "")
        else:
            if i == 0:
                result = None
            else:
                k = failure[i - 1]
                outcome = delta(k, a)
                if outcome == None:
                    result = None
                else:
                    nxt, out = outcome
                    # Flush the part of the buffer
                    result = (nxt, s1[:i-nxt+1])
        
        delta_memo[key] = result
        return result

    specs = []
    X = set(s1)
    
    for i in range(m):
        # Add explicit transition for the "good" letter.
        outcome_good = delta(i, s1[i])
        specs.append((i, s1[i], outcome_good[1], outcome_good[0]))
        
        # For letters in s1 (other than the good letter) that yield a non-generic outcome,
        # add an explicit transition.
        for a in X:
            if a == s1[i]:
                continue
            outcome = delta(i, a)
            if outcome != None:
                specs.append((i, a, outcome[1], outcome[0]))
    
    buffer_specs = []
    for spec in specs:
        src, in_spec, _, tgt = spec
        new_src = src + m if src != 0 else 0
        if tgt == 0:
            buffer_specs.append((new_src, in_spec, "", -1)) # abort
        else:
            buffer_specs.append((new_src, in_spec, "$self", tgt + m))

    for i in range(1, m):
        buffer_specs.append((i+m, "$other", "$self", 0))

    specs.extend(buffer_specs)
    specs.append((0, "$other", "$self", 0))
    final_states = {0} | {i + m for i in range(1, m)}
    return create_fst(specs, start_state=0, final_states=final_states)

def first_replacement_FST(s1: str, s2: str) -> FST:
    m = len(s1)
    if m == 0:
        raise ValueError("s1 must be nonempty")
    
    # Compute the KMP failure function for s1.
    failure = [0] * m
    for i in range(1, m):
        j = failure[i - 1]
        while j > 0 and s1[i] != s1[j]:
            j = failure[j - 1]
        if s1[i] == s1[j]:
            j += 1
        failure[i] = j

    delta_memo = {}
    
    def delta(i, a) -> Optional[Tuple[int, str]]:
        key = (i, a)
        if key in delta_memo:
            return delta_memo[key]
            
        result = None
        if a == s1[i]:
            if i == m - 1:
                # Full match: output s2 and go to the success state.
                result = (-2, s2)
            else:
                result = (i + 1, "")
        else:
            if i == 0:
                result = None
            else:
                k = failure[i - 1]
                outcome = delta(k, a)
                if outcome == None:
                    result = None
                else:
                    nxt, out = outcome
                    # Flush the part of the buffer
                    result = (nxt, s1[:i-nxt+1])
        
        delta_memo[key] = result
        return result

    specs = []
    X = set(s1)
    
    for i in range(m):
        # Add explicit transition for the "good" letter.
        outcome_good = delta(i, s1[i])
        specs.append((i, s1[i], outcome_good[1], outcome_good[0]))
        
        # For letters in s1 (other than the good letter) that yield a non-generic outcome,
        # add an explicit transition.
        for a in X:
            if a == s1[i]:
                continue
            outcome = delta(i, a)
            if outcome != None:
                specs.append((i, a, outcome[1], outcome[0]))
    
    buffer_specs = []
    for spec in specs:
        src, in_spec, _, tgt = spec
        new_src = src + m if src != 0 else 0
        if tgt == 0 or tgt == -2:
            buffer_specs.append((new_src, in_spec, "", -1)) # abort
        else:
            buffer_specs.append((new_src, in_spec, "$self", tgt + m))

    for i in range(1, m):
        buffer_specs.append((i+m, "$other", "$self", 0))

    specs.extend(buffer_specs)
    specs.append((0, "$other", "$self", 0))
    specs.append((-2, "$other", "$self", -2))
    final_states = {0, -2} | {i + m for i in range(1, m)}
    return create_fst(specs, start_state=0, final_states=final_states)


def global_regex_replacement_FST(automaton: Automaton, s2: str) -> FST:

    def check_fallback(trans: Transition, automata: Automaton) -> List[Tuple[str, str]]:
        if trans.getDest().isAccept():
            return []
        intersentions = []
        min_char = trans.getMin()
        max_char = trans.getMax()
        automata_initial_state = automata.getInitialState()
        for t in automata_initial_state.getSortedTransitions(True):
            if ord(t.getMax()) >= ord(min_char) and ord(t.getMin()) <= ord(max_char):
                new_min = min_char if ord(min_char) > ord(t.getMin()) else t.getMin()
                new_max = max_char if ord(max_char) < ord(t.getMax()) else t.getMax()
                a = automata.clone()
                b = automata.clone()
                a.setInitialState(t.getDest())
                b.setInitialState(trans.getDest())
                if not a.subsetOf(b):
                    intersentions.append((new_min, new_max))
        return intersentions



    # FIXME: incorrect leftmost longest match: can handle: aa?; but cannot handle a(aa)?
    # FIXME: there is no failure function for regex now: cannot handle repalce a.a with x in aaba
    # FIXME: cannot handle regex that contains empty string: replace a* with b in ac, should be bcb

    # 5 modes
    # match: the original automaton i
    # buffer: the buffer automaton i + num_states
    # success: the success automaton i + 2 * num_states
    # buffer success: the success automaton i + 3 * num_states
    # longest buffer success: the success automaton i + 4 * num_states
    # new initial state: -1
    # abort state: -2
    automaton.determinize()
    automaton.minimize()
    automaton.removeDeadTransitions()
    if automaton.isEmpty():
        raise ToolError("pattern regex is empty")
    if automaton.isEmptyString():
        raise ToolError("pattern regex is empty string")
    # pattern = automaton.getSingleton()
    # if pattern is None:
    #     return global_replacement_FST(pattern, s2)
    state_map: Dict[State, int] = {}
    specs = []
    states = automaton.getStates()
    num_states = len(states)
    for i, state in enumerate(states):
        state_map[state] = i
    initial_state = state_map[automaton.getInitialState()]
    new_initial_state = -1
    abort_state = -2
    final_states = {state_map[state] for state in automaton.getAcceptStates()}
    for state in automaton.getStates():
        state_id = state_map[state]
        for trans in state.getSortedTransitions(True):
            min_char = trans.getMin()
            max_char = trans.getMax()
            input_range = min_char + "--" + max_char
            dest_state_id = state_map[trans.getDest()]
            # match mode
            if state_id not in final_states:
                if dest_state_id in final_states:
                    if state_id == initial_state:
                        specs.append((new_initial_state, input_range, "", dest_state_id + 2 * num_states))
                        specs.append((new_initial_state, input_range, s2, dest_state_id + 3 * num_states))
                    specs.append((state_id, input_range, "", dest_state_id + 2 * num_states))
                    specs.append((state_id, input_range, s2, dest_state_id + 3 * num_states))
                else: # if the destination state is not final state
                    if state_id == initial_state:
                        specs.append((new_initial_state, input_range, "", dest_state_id))
                    specs.append((state_id, input_range, "", dest_state_id))
            elif state_id == initial_state: # if the initial state is final state
                if dest_state_id in final_states:
                    specs.append((new_initial_state, input_range, "", dest_state_id + 2 * num_states))
                    specs.append((new_initial_state, input_range, s2, dest_state_id + 3 * num_states))
                
            
            # buffer mode
            if state_id not in final_states: # abort because buffer is not needed
                if dest_state_id not in final_states:
                    if state_id == initial_state:
                        specs.append((new_initial_state, input_range, "$self", dest_state_id + num_states))
                    specs.append((state_id + num_states, input_range, "$self", dest_state_id + num_states))
                    # non-deteministic guess
                    intersentions = check_fallback(trans, automaton)
                    for new_min, new_max in intersentions:
                        specs.append((state_id + num_states, new_min + "--" + new_max, "", new_initial_state, True))
                else:
                    specs.append((state_id + num_states, input_range, "$self", abort_state))
            
            # success mode
            specs.append((state_id + 2 * num_states, input_range, "", dest_state_id + 2 * num_states))
            if dest_state_id not in final_states and state_id in final_states:
                specs.append((state_id + 2 * num_states, input_range, s2 + "$self", dest_state_id + 4 * num_states))
                specs.append((state_id + 2 * num_states, input_range, s2, new_initial_state, True))

            # buffer success mode
            specs.append((state_id + 3 * num_states, input_range, "", dest_state_id + 3 * num_states))

            # longest buffer success mode
            if dest_state_id not in final_states:
                specs.append((state_id + 4 * num_states, input_range, "$self", dest_state_id + 4 * num_states))
            else:
                specs.append((state_id + 4 * num_states, input_range, "", abort_state))
    
    for state in automaton.getStates():
        state_id = state_map[state]
        if state_id in final_states:
            # success mode return to end state
            specs.append((state_id + 2 * num_states, "$other", s2, new_initial_state, True))
        else:
            # buffer mode return to initial state
            specs.append((state_id + num_states, "$other", "", new_initial_state, True))
            # longest buffer success mode return to end state
            specs.append((state_id + 4 * num_states, "$other", "", new_initial_state, True))


    if initial_state not in final_states:
        specs.append((new_initial_state, "$other", "$self", new_initial_state))
    else:
        specs.append((new_initial_state, "$other", "$self" + s2, new_initial_state))
    
    final_states = {new_initial_state} | {i + 3 * num_states for i in final_states} | {i + num_states for i in range(num_states)} |  {i + 4 * num_states for i in range(num_states) if i not in final_states}
        
    return create_fst(specs, start_state=new_initial_state, final_states=final_states)



def first_regex_replacement_FST(automaton: Automaton, s2: str) -> FST:
    def check_fallback(trans: Transition, automata: Automaton) -> List[Tuple[str, str]]:
        if trans.getDest().isAccept():
            return []
        intersentions = []
        min_char = trans.getMin()
        max_char = trans.getMax()
        automata_initial_state = automata.getInitialState()
        for t in automata_initial_state.getSortedTransitions(True):
            if ord(t.getMax()) >= ord(min_char) and ord(t.getMin()) <= ord(max_char):
                new_min = min_char if ord(min_char) > ord(t.getMin()) else t.getMin()
                new_max = max_char if ord(max_char) < ord(t.getMax()) else t.getMax()
                a = automata.clone()
                b = automata.clone()
                a.setInitialState(t.getDest())
                b.setInitialState(trans.getDest())
                if not a.subsetOf(b):
                    intersentions.append((new_min, new_max))
        return intersentions
    # FIXME: there is no failure function for regex now: cannot handle repalce a.a with x in aaba
    # FIXME: cannot handle regex that contains empty string: replace a* with b in ac, should be bcb

    # 5 modes
    # match: the original automaton i
    # buffer: the buffer automaton i + num_states
    # success: the success automaton i + 2 * num_states
    # buffer success: the success automaton i + 3 * num_states
    # longest buffer success: the success automaton i + 4 * num_states
    # new initial state: -1
    # abort state: -2
    # end state: -3
    if automaton.isEmpty():
        raise ToolError("pattern regex is empty")
    if automaton.isEmptyString():
        raise ToolError("pattern regex is empty string")
    # pattern = automaton.getSingleton()
    # if pattern is None:
    #     return global_replacement_FST(pattern, s2)
    state_map: Dict[State, int] = {}
    specs = []
    states = automaton.getStates()
    num_states = len(states)
    for i, state in enumerate(states):
        state_map[state] = i
    initial_state = state_map[automaton.getInitialState()]
    new_initial_state = -1
    abort_state = -2
    end_state = -3
    final_states = {state_map[state] for state in automaton.getAcceptStates()}
    for state in automaton.getStates():
        state_id = state_map[state]
        for trans in state.getSortedTransitions(True):
            min_char = trans.getMin()
            max_char = trans.getMax()
            input_range = min_char + "--" + max_char
            dest_state_id = state_map[trans.getDest()]
            # match mode
            if state_id not in final_states:
                if dest_state_id in final_states:
                    if state_id == initial_state:
                        specs.append((new_initial_state, input_range, "", dest_state_id + 2 * num_states))
                        specs.append((new_initial_state, input_range, s2, dest_state_id + 3 * num_states))
                    specs.append((state_id, input_range, "", dest_state_id + 2 * num_states))
                    specs.append((state_id, input_range, s2, dest_state_id + 3 * num_states))
                else: # if the destination state is not final state
                    if state_id == initial_state:
                        specs.append((new_initial_state, input_range, "", dest_state_id))
                    specs.append((state_id, input_range, "", dest_state_id))
            elif state_id == initial_state: # if the initial state is final state
                if dest_state_id in final_states:
                    specs.append((new_initial_state, input_range, "", dest_state_id + 2 * num_states))
                    specs.append((new_initial_state, input_range, s2, dest_state_id + 3 * num_states))
                
            
            # buffer mode
            if state_id not in final_states: # abort because buffer is not needed
                if dest_state_id not in final_states:
                    if state_id == initial_state:
                        specs.append((new_initial_state, input_range, "$self", dest_state_id + num_states))
                    specs.append((state_id + num_states, input_range, "$self", dest_state_id + num_states))
                    # non-deteministic guess
                    intersentions = check_fallback(trans, automaton)
                    for new_min, new_max in intersentions:
                        specs.append((state_id + num_states, new_min + "--" + new_max, "", new_initial_state, True))
                else:
                    specs.append((state_id + num_states, input_range, "$self", abort_state))
            
            # success mode
            specs.append((state_id + 2 * num_states, input_range, "", dest_state_id + 2 * num_states))
            if dest_state_id not in final_states and state_id in final_states:
                specs.append((state_id + 2 * num_states, input_range, s2 + "$self", dest_state_id + 4 * num_states))

            # buffer success mode
            specs.append((state_id + 3 * num_states, input_range, "", dest_state_id + 3 * num_states))

            # longest buffer success mode
            if dest_state_id not in final_states:
                specs.append((state_id + 4 * num_states, input_range, "$self", dest_state_id + 4 * num_states))
            else:
                specs.append((state_id + 4 * num_states, input_range, "", abort_state))
    
    for state in automaton.getStates():
        state_id = state_map[state]
        if state_id in final_states:
            # success mode return to end state
            specs.append((state_id + 2 * num_states, "$other", s2 + "$self", end_state))
        else:
            # buffer mode return to initial state
            specs.append((state_id + num_states, "$other", "", new_initial_state, True))
            # longest buffer success mode return to end state
            specs.append((state_id + 4 * num_states, "$other", "$self", end_state))


    if initial_state not in final_states:
        specs.append((new_initial_state, "$other", "$self", new_initial_state))
    else:
        specs.append((new_initial_state, "$other", "$self" + s2, end_state))

    specs.append((end_state, "$other", "$self", end_state))
    
    final_states = {new_initial_state} | {i + 3 * num_states for i in final_states} | {i + num_states for i in range(num_states)} | {end_state} |  {i + 4 * num_states for i in range(num_states) if i not in final_states}
        
    return create_fst(specs, start_state=new_initial_state, final_states=final_states)


def start_regex_replacement_FST(automaton: Automaton, s2: str) -> FST:
    # FIXME: cannot handle regex that contains empty string: replace a* with b in ac, should be bcb

    # 5 modes
    # match: the original automaton i
    # buffer: the buffer automaton i + num_states
    # success: the success automaton i + 2 * num_states
    # buffer success: the success automaton i + 3 * num_states
    # longest buffer success: the success automaton i + 4 * num_states
    # new initial state: -1
    # abort state: -2
    # end state: -3
    if automaton.isEmpty():
        raise ToolError("pattern regex is empty")
    if automaton.isEmptyString():
        raise ToolError("pattern regex is empty string")
    # pattern = automaton.getSingleton()
    # if pattern is None:
    #     return global_replacement_FST(pattern, s2)
    state_map: Dict[State, int] = {}
    specs = []
    states = automaton.getStates()
    num_states = len(states)
    for i, state in enumerate(states):
        state_map[state] = i
    initial_state = state_map[automaton.getInitialState()]
    new_initial_state = -1
    abort_state = -2
    end_state = -3
    final_states = {state_map[state] for state in automaton.getAcceptStates()}
    for state in automaton.getStates():
        state_id = state_map[state]
        for trans in state.getSortedTransitions(True):
            min_char = trans.getMin()
            max_char = trans.getMax()
            input_range = min_char + "--" + max_char
            dest_state_id = state_map[trans.getDest()]
            # match mode
            if state_id not in final_states:
                if dest_state_id in final_states:
                    if state_id == initial_state:
                        specs.append((new_initial_state, input_range, "", dest_state_id + 2 * num_states))
                        specs.append((new_initial_state, input_range, s2, dest_state_id + 3 * num_states))
                    specs.append((state_id, input_range, "", dest_state_id + 2 * num_states))
                    specs.append((state_id, input_range, s2, dest_state_id + 3 * num_states))
                else: # if the destination state is not final state
                    if state_id == initial_state:
                        specs.append((new_initial_state, input_range, "", dest_state_id))
                    specs.append((state_id, input_range, "", dest_state_id))
            elif state_id == initial_state: # if the initial state is final state
                if dest_state_id in final_states:
                    specs.append((new_initial_state, input_range, "", dest_state_id + 2 * num_states))
                    specs.append((new_initial_state, input_range, s2, dest_state_id + 3 * num_states))
                
            
            # buffer mode
            if state_id not in final_states: # abort because buffer is not needed
                if dest_state_id not in final_states:
                    if state_id == initial_state:
                        specs.append((new_initial_state, input_range, "$self", dest_state_id + num_states))
                    specs.append((state_id + num_states, input_range, "$self", dest_state_id + num_states))
                else:
                    specs.append((state_id + num_states, input_range, "$self", abort_state))
            
            # success mode
            specs.append((state_id + 2 * num_states, input_range, "", dest_state_id + 2 * num_states))
            if dest_state_id not in final_states and state_id in final_states:
                specs.append((state_id + 2 * num_states, input_range, s2 + "$self", dest_state_id + 4 * num_states))

            # buffer success mode
            specs.append((state_id + 3 * num_states, input_range, "", dest_state_id + 3 * num_states))

            # longest buffer success mode
            if dest_state_id not in final_states:
                specs.append((state_id + 4 * num_states, input_range, "$self", dest_state_id + 4 * num_states))
            else:
                specs.append((state_id + 4 * num_states, input_range, "", abort_state))
    
    for state in automaton.getStates():
        state_id = state_map[state]
        if state_id in final_states:
            # success mode return to end state
            specs.append((state_id + 2 * num_states, "$other", s2 + "$self", end_state))
        else:
            # buffer mode return to initial state
            specs.append((state_id + num_states, "$other", "$self", end_state))
            # longest buffer success mode return to end state
            specs.append((state_id + 4 * num_states, "$other", "$self", end_state))


    if initial_state not in final_states:
        specs.append((new_initial_state, "$other", "$self", end_state))
    else:
        specs.append((new_initial_state, "$other", "$self" + s2, end_state))

    specs.append((end_state, "$other", "$self", end_state))
    
    final_states = {new_initial_state} | {i + 3 * num_states for i in final_states} | {i + num_states for i in range(num_states)} | {end_state} |  {i + 4 * num_states for i in range(num_states) if i not in final_states}
        
    return create_fst(specs, start_state=new_initial_state, final_states=final_states)


def global_regex_extract_FST(automaton: Automaton) -> FST:

    def check_fallback(trans: Transition, automata: Automaton) -> List[Tuple[str, str]]:
        if trans.getDest().isAccept():
            return []
        intersentions = []
        min_char = trans.getMin()
        max_char = trans.getMax()
        automata_initial_state = automata.getInitialState()
        for t in automata_initial_state.getSortedTransitions(True):
            if ord(t.getMax()) >= ord(min_char) and ord(t.getMin()) <= ord(max_char):
                new_min = min_char if ord(min_char) > ord(t.getMin()) else t.getMin()
                new_max = max_char if ord(max_char) < ord(t.getMax()) else t.getMax()
                a = automata.clone()
                b = automata.clone()
                a.setInitialState(t.getDest())
                b.setInitialState(trans.getDest())
                if not a.subsetOf(b):
                    intersentions.append((new_min, new_max))
        return intersentions



    # FIXME: incorrect leftmost longest match: can handle: aa?; but cannot handle a(aa)?
    # FIXME: there is no failure function for regex now: cannot handle repalce a.a with x in aaba
    # FIXME: cannot handle regex that contains empty string: replace a* with b in ac, should be bcb

    # 5 modes
    # match: the original automaton i
    # buffer: the buffer automaton i + num_states
    # success: the success automaton i + 2 * num_states
    # buffer success: the success automaton i + 3 * num_states
    # longest buffer success: the success automaton i + 4 * num_states
    # new initial state: -1
    # abort state: -2
    # end state: -3
    automaton.determinize()
    automaton.minimize()
    automaton.removeDeadTransitions()
    if automaton.isEmpty():
        raise ToolError("pattern regex is empty")
    if automaton.isEmptyString():
        raise ToolError("pattern regex is empty string")
    # pattern = automaton.getSingleton()
    # if pattern is None:
    #     return global_replacement_FST(pattern, s2)
    state_map: Dict[State, int] = {}
    specs = []
    states = automaton.getStates()
    num_states = len(states)
    for i, state in enumerate(states):
        state_map[state] = i
    initial_state = state_map[automaton.getInitialState()]
    new_initial_state = -1
    abort_state = -2
    end_state = -3
    final_states = {state_map[state] for state in automaton.getAcceptStates()}
    for state in automaton.getStates():
        state_id = state_map[state]
        for trans in state.getSortedTransitions(True):
            min_char = trans.getMin()
            max_char = trans.getMax()
            input_range = min_char + "--" + max_char
            dest_state_id = state_map[trans.getDest()]
            # match mode
            if state_id not in final_states:
                if dest_state_id in final_states:
                    if state_id == initial_state:
                        specs.append((new_initial_state, input_range, "$self", dest_state_id + 2 * num_states))
                    specs.append((state_id, input_range, "$self", dest_state_id + 2 * num_states))
                else: # if the destination state is not final state
                    if state_id == initial_state:
                        specs.append((new_initial_state, input_range, "$self", dest_state_id))
                    specs.append((state_id, input_range, "$self", dest_state_id))
                
            
            # buffer mode
            if state_id not in final_states: # abort because buffer is not needed
                if dest_state_id not in final_states:
                    if state_id == initial_state:
                        specs.append((new_initial_state, input_range, "", dest_state_id + num_states))
                    specs.append((state_id + num_states, input_range, "", dest_state_id + num_states))
                    # non-deteministic guess
                    intersentions = check_fallback(trans, automaton)
                    for new_min, new_max in intersentions:
                        specs.append((state_id + num_states, new_min + "--" + new_max, "", new_initial_state, True))
                else:
                    specs.append((state_id + num_states, input_range, "", dest_state_id + 3 * num_states))
            
            # success mode
            specs.append((state_id + 2 * num_states, input_range, "$self", dest_state_id + 2 * num_states))
            if dest_state_id not in final_states and state_id in final_states:
                specs.append((state_id + 2 * num_states, input_range, "", dest_state_id + 4 * num_states))

            # buffer success mode
            specs.append((state_id + 3 * num_states, input_range, "", dest_state_id + 3 * num_states))
            if dest_state_id not in final_states and state_id in final_states:
                specs.append((state_id + 3 * num_states, input_range, "", new_initial_state, True))

            # longest buffer success mode
            if dest_state_id not in final_states:
                specs.append((state_id + 4 * num_states, input_range, "", dest_state_id + 4 * num_states))
            else:
                specs.append((state_id + 4 * num_states, input_range, "", abort_state))
    
    for state in automaton.getStates():
        state_id = state_map[state]
        if state_id in final_states:
            # success mode return to end state
            specs.append((state_id + 2 * num_states, "$other", "", end_state))
        else:
            # longest buffer success mode return to end state
            specs.append((state_id + 4 * num_states, "$other", "", end_state))

        # buffer success mode return to initial state
        specs.append((state_id + 3 * num_states, "$other", "", new_initial_state, True))
        # buffer mode return to initial state
        specs.append((state_id + num_states, "$other", "", new_initial_state, True))

    specs.append((end_state, "$other", "", end_state))

    specs.append((new_initial_state, "$other", "", new_initial_state))
    
    final_states = {end_state} | {i + 3 * num_states for i in final_states} |  {i + 4 * num_states for i in range(num_states) if i not in final_states}
        
    return create_fst(specs, start_state=new_initial_state, final_states=final_states)


def start_regex_extract_FST(automaton: Automaton) -> FST:
    # FIXME: cannot handle regex that contains empty string: replace a* with b in ac, should be bcb

    # 5 modes
    # match: the original automaton i
    # buffer: the buffer automaton i + num_states
    # success: the success automaton i + 2 * num_states
    # buffer success: the success automaton i + 3 * num_states
    # longest buffer success: the success automaton i + 4 * num_states
    # new initial state: -1
    # abort state: -2
    # end state: -3
    if automaton.isEmpty():
        raise ToolError("pattern regex is empty")
    if automaton.isEmptyString():
        raise ToolError("pattern regex is empty string")
    # pattern = automaton.getSingleton()
    # if pattern is None:
    #     return global_replacement_FST(pattern, s2)
    state_map: Dict[State, int] = {}
    specs = []
    states = automaton.getStates()
    num_states = len(states)
    for i, state in enumerate(states):
        state_map[state] = i
    initial_state = state_map[automaton.getInitialState()]
    new_initial_state = -1
    abort_state = -2
    end_state = -3
    final_states = {state_map[state] for state in automaton.getAcceptStates()}
    for state in automaton.getStates():
        state_id = state_map[state]
        for trans in state.getSortedTransitions(True):
            min_char = trans.getMin()
            max_char = trans.getMax()
            input_range = min_char + "--" + max_char
            dest_state_id = state_map[trans.getDest()]
            # match mode
            if state_id not in final_states:
                if dest_state_id in final_states:
                    if state_id == initial_state:
                        specs.append((new_initial_state, input_range, "$self", dest_state_id + 2 * num_states))
                    specs.append((state_id, input_range, "$self", dest_state_id + 2 * num_states))
                else: # if the destination state is not final state
                    if state_id == initial_state:
                        specs.append((new_initial_state, input_range, "$self", dest_state_id))
                    specs.append((state_id, input_range, "$self", dest_state_id))
                
            
            # buffer mode
            if state_id not in final_states: # abort because buffer is not needed
                if dest_state_id not in final_states:
                    if state_id == initial_state:
                        specs.append((new_initial_state, input_range, "", dest_state_id + num_states))
                    specs.append((state_id + num_states, input_range, "", dest_state_id + num_states))
                else:
                    specs.append((state_id + num_states, input_range, "", dest_state_id + 3 * num_states))
            
            # success mode
            specs.append((state_id + 2 * num_states, input_range, "$self", dest_state_id + 2 * num_states))
            if dest_state_id not in final_states and state_id in final_states:
                specs.append((state_id + 2 * num_states, input_range, "", dest_state_id + 4 * num_states))

            # buffer success mode
            specs.append((state_id + 3 * num_states, input_range, "", dest_state_id + 3 * num_states))

            # longest buffer success mode
            if dest_state_id not in final_states:
                specs.append((state_id + 4 * num_states, input_range, "", dest_state_id + 4 * num_states))
            else:
                specs.append((state_id + 4 * num_states, input_range, "", abort_state))
    
    for state in automaton.getStates():
        state_id = state_map[state]
        if state_id in final_states:
            # success mode return to end state
            specs.append((state_id + 2 * num_states, "$other", "", end_state))
        else:
            # longest buffer success mode return to end state
            specs.append((state_id + 4 * num_states, "$other", "", end_state))

    specs.append((end_state, "$other", "", end_state))
    
    final_states = {end_state} | {i + 3 * num_states for i in final_states} |  {i + 4 * num_states for i in range(num_states) if i not in final_states}
        
    return create_fst(specs, start_state=new_initial_state, final_states=final_states)


def global_regex_replacement(input_automata: Automaton, pattern: Automaton, replacement: str, capture_automatas: List[Automaton]) -> Automaton:
    capture_refs = re.findall(r'\\(\d+)', replacement)
    if not capture_refs:
        fst = global_regex_replacement_FST(pattern, replacement)
        return product_fst_automaton(fst, input_automata)

    # Use characters from Private Use Area
    capture_chars = [chr(0xE000 + i * 2 + 1) for i in len(capture_automatas)]
    alphabet = "[^" + "".join(capture_chars) + "]"
    replacement_mapped = replacement
    for i, char in enumerate(capture_chars, 1):
        replacement_mapped = replacement_mapped.replace(f"\\{i}", char)

    new_input_automata = input_automata.intersection(RegExp(alphabet).toAutomaton())
    
    # Build FST for the pattern with capture group outputs replaced with our mapping chars
    fst = global_regex_replacement_FST(pattern, replacement_mapped)
    product = product_fst_automaton(fst, new_input_automata)
    
    result = Automaton()
    product_to_result = {product.getInitialState(): result.getInitialState()}
    for state in product.getStates():
        if state not in product_to_result:
            product_to_result[state] = State()
            product_to_result[state].setAccept(state.isAccept())

    # traverse the result automaton and replace the mapping chars with the capture group automata
    empty_transitions: Set[Tuple[State, State]] = set()
    for state in product.getStates():
        for trans in state.getTransitions():
            min_in = trans.getMin()
            max_in = trans.getMax()
            if ord(max_in) < 0xE000:
                product_to_result[state].addTransition(Transition(min_in, max_in, product_to_result[trans.getDest()]))
                continue
            if ord(min_in) < 0xE000:
                product_to_result[state].addTransition(Transition(min_in, chr(0xE000 - 1), product_to_result[trans.getDest()]))
            min_in = chr(max(ord(min_in), 0xE000))
            for i, char in enumerate(capture_chars, 1):
                if ord(min_in) <= ord(char) <= ord(max_in):
                    automaton = capture_automatas[i - 1].clone()
                    empty_transitions.add((product_to_result[state], automaton.getInitialState()))
                    final_states = automaton.getAcceptStates()
                    for final_state in final_states:
                        empty_transitions.add((final_state, product_to_result[trans.getDest()]))
                if ord(min_in) <= ord(char) - 1 <= ord(max_in):
                    product_to_result[state].addTransition(Transition(min_in, chr(ord(char)), product_to_result[trans.getDest()]))
                min_in = chr(max(ord(min_in), ord(char) + 1))
            if ord(min_in) <= ord(max_in):
                product_to_result[state].addTransition(Transition(min_in, max_in, product_to_result[trans.getDest()]))

    process_empty_transitions(empty_transitions)
    result.setDeterministic(False)
    result.removeDeadTransitions()
    result.minimize()
    return result



    

if __name__ == '__main__':
    regex = RegExp("[P-Z]+[a-z][0-9]+")
    automaton = regex.toAutomaton()
    specs = [
        (0, "a--z", "A--Z", 0),
        (0, 'A--Z', '0--9', 0),
        (0, "a", "a", 0),
        (0, "$other", "$self", 0),
        (0, "$other", "a", 0),
    ]
    fst = create_fst(specs, start_state=0, final_states={0})
    # test_str = "asdasdasdas"
    # print(fst.transform_all(test_str))
    product = product_fst_automaton(fst, automaton)
    print(product)
    print(product.run("X"))



    #   transitions = [
    #     ('q0', 'b', 'b', 'q0'),
    #     ('q0', 'x', 'x', 'q0'),
    #     ('q0', 'a', '', 'q11'),
    #     ('q0', 'a', 'a', 'q21'),
    #     ('q0', 'a', 'a', 'q31'),
    #     ('q11', 'a', '', 'q11'),
    #     ('q21', 'a', 'a', 'q21'),
    #     ('q31', 'a', 'a', 'q31'),
    #     ('q11', 'b', '', 'q12'),
    #     ('q21', 'b', 'b', 'q22'),
    #     ('q31', 'b', 'b', 'q32'),
    #     ('q12', 'a', '', 'q13'),
    #     ('q22', 'a', '', 'q23'),
    #     ('q32', 'a', 'a', 'q33'),
    #     ('q13', 'a', 'x', 'q0'),
    #     ('q23', 'b', '', 'q12'),
    #     ('q33', 'b', 'b', 'q22'),
    #     ('q33', 'b', 'b', 'q32'),
    #     ('q33', 'x', 'x', 'q0'),
    #     ('q32', 'x', 'x', 'q0'),
    #     ('q32', 'b', 'b', 'q0'),
    #     ('q31', 'x', 'x', 'q0'),
    # ]
