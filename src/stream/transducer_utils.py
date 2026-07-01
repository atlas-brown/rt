import re
from abc import ABC, abstractmethod
from collections import deque
from typing import Callable, Deque, Dict, List, Optional, Set, Tuple

from stream.config.global_config import CONFIG
from stream.java_api import Automaton, RegExp, State, Transition
from stream.tool_error import ToolError

from stream.constants import alphabet_size

class OutputType(ABC):
    
    @abstractmethod
    def to_string(self) -> str:
        pass

class LiteralOutput(OutputType):
    
    def __init__(self, value: str):
        self.value = value
    
    def to_string(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"LiteralOutput({self.value!r})"

class SelfOutput(OutputType):
    
    def to_string(self) -> str:
        return "$self"
    
    def __repr__(self) -> str:
        return "SelfOutput()"

class VariableOutput(OutputType):
    """Output containing $self variables"""
    
    def __init__(self, template: str):
        self.template = template
        if "$self" not in template:
            raise ValueError("VariableOutput must contain $self")
    
    def to_string(self) -> str:
        return self.template
    
    def __repr__(self) -> str:
        return f"VariableOutput({self.template!r})"

class RangeOutput(OutputType):
    """One-to-one range output (A--Z)"""
    
    def __init__(self, min_char: str, max_char: str):
        self.min_char = min_char
        self.max_char = max_char
        if ord(min_char) > ord(max_char):
            raise ValueError(f"Invalid range: {min_char}--{max_char}")
    
    def to_string(self) -> str:
        return f"{self.min_char}--{self.max_char}"
    
    def __repr__(self) -> str:
        return f"RangeOutput({self.min_char!r}, {self.max_char!r})"

class FullRangeOutput(OutputType):
    """Full range output (*A--Z) - one input can produce any char in range"""
    
    def __init__(self, min_char: str, max_char: str):
        self.min_char = min_char
        self.max_char = max_char
        if ord(min_char) > ord(max_char):
            raise ValueError(f"Invalid range: {min_char}--{max_char}")
    
    def to_string(self) -> str:
        return f"*{self.min_char}--{self.max_char}"
    
    def __repr__(self) -> str:
        return f"FullRangeOutput({self.min_char!r}, {self.max_char!r})"

def parse_output(output_str: str) -> OutputType:
    if output_str == "$self":
        return SelfOutput()
    elif "$self" in output_str:
        return VariableOutput(output_str)
    elif output_str.startswith("*") and len(output_str) == 5:
        # Full range output
        range_spec = output_str[1:]
        if range_spec.startswith("---"):
            return FullRangeOutput("-", range_spec[3:])
        elif range_spec.endswith("---"):
            return FullRangeOutput(range_spec[:-3], "-")
        elif "--" in range_spec:
            parts = range_spec.split("--")
            if len(parts) == 2:
                return FullRangeOutput(parts[0], parts[1])
        raise ValueError(f"Invalid full range output: {output_str}")
    elif "--" in output_str:
        # One-to-one range output
        if output_str.startswith("---"):
            return RangeOutput("-", output_str[3:])
        elif output_str.endswith("---"):
            return RangeOutput(output_str[:-3], "-")
        else:
            parts = output_str.split("--")
            if len(parts) == 2:
                return RangeOutput(parts[0], parts[1])
        raise ValueError(f"Invalid range output: {output_str}")
    else:
        return LiteralOutput(output_str)

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
    def __init__(self, min: Optional[str], max: Optional[str], output: str | OutputType, to: FST_State, is_other: bool = False, is_not_consumed = False, is_epsilon: bool = False) -> None:
        self.min: Optional[str] = min
        self.max: Optional[str] = max
        
        if isinstance(output, str):
            self.output_type: OutputType = parse_output(output)
        else:
            self.output_type: OutputType = output
            
        # Keep legacy string property for backward compatibility
        self.output: str = self.output_type.to_string()
        
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

    def __repr__(self) -> str:
        if self.is_epsilon:
            return f"FST_Transition(min='', max='', out='{self.output}', to={self.to.id})"
        
        if isinstance(self.output_type, FullRangeOutput):
            return f"FST_Transition(min={ord(self.min)}, max={ord(self.max)}, out={self.output_type}, to={self.to.id})"
        elif isinstance(self.output_type, VariableOutput):
            return f"FST_Transition(min={ord(self.min)}, max={ord(self.max)}, out={self.output_type}, to={self.to.id})"
        elif isinstance(self.output_type, SelfOutput):
            return f"FST_Transition(min={ord(self.min)}, max={ord(self.max)}, out={self.output_type}, to={self.to.id})"
        elif isinstance(self.output_type, RangeOutput):
            return f"FST_Transition(min={ord(self.min)}, max={ord(self.max)}, out={self.output_type}, to={self.to.id})"
        elif isinstance(self.output_type, LiteralOutput):
            return f"FST_Transition(min={ord(self.min)}, max={ord(self.max)}, out={self.output_type}, to={self.to.id})"
        else:
            raise ValueError(f"Unsupported output type: {type(self.output_type)}")


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
        if min_in == "$epsilon":
            is_epsilon = True
            start_val, end_val = None, None
        elif min_in == "$other":
            is_other = True
            start_val, end_val = None, None
        elif min_in == "$all":
            start_val, end_val = chr(0), chr(alphabet_size)
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

    def _compute_complement_intervals(self, intervals: List[Tuple[int, int]], min_val: int = 0, max_val: int = alphabet_size) -> List[Tuple[int, int]]:
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
                    raise ValueError(f"Cannot eliminate not_consumed transition: target state {target_state.id} has not_consumed or epsilon transitions")
                
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
        
        MAX_CONFIGURATIONS = 10000
        MAX_EPSILON_ITERATIONS = 1000

        def epsilon_closure(configurations: Set[Tuple[FST_State, str]]) -> Set[Tuple[FST_State, str]]:
            closure = set(configurations)
            iteration_count = 0
            changed = True
            while changed and iteration_count < MAX_EPSILON_ITERATIONS:
                iteration_count += 1
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
                                if len(closure) + len(new_configs) > MAX_CONFIGURATIONS:
                                    raise RuntimeError(f"FST transform explosion: too many configurations (>{MAX_CONFIGURATIONS})")
                closure.update(new_configs)
            
            if iteration_count >= MAX_EPSILON_ITERATIONS:
                raise RuntimeError(f"FST epsilon cycle detected: exceeded {MAX_EPSILON_ITERATIONS} iterations")
            
            return closure
        
        configurations: Set[Tuple[FST_State, str]] = epsilon_closure({(self.initial, "")})
        
        for c in input_string:
            next_configurations: Set[Tuple[FST_State, str]] = set()
            for state, output_so_far in configurations:
                for trans in state.transitions:
                    if not trans.is_epsilon and trans.applies(c):
                        new_state = trans.to
                        if trans.is_epsilon:
                            transformed_outputs = [trans.output_type.to_string()]
                        elif isinstance(trans.output_type, SelfOutput):
                            transformed_outputs = [c]
                        elif isinstance(trans.output_type, LiteralOutput):
                            transformed_outputs = [trans.output_type.value]
                        elif isinstance(trans.output_type, VariableOutput):
                            transformed_outputs = [trans.output_type.template.replace("$self", c)]
                        elif isinstance(trans.output_type, RangeOutput):
                            input_offset = ord(c) - ord(trans.min)
                            output_char = chr(ord(trans.output_type.min_char) + input_offset)
                            # Clamp to max if needed
                            transformed_outputs = [chr(min(ord(output_char), ord(trans.output_type.max_char)))]
                        elif isinstance(trans.output_type, FullRangeOutput):
                            transformed_outputs = []
                            for char_code in range(ord(trans.output_type.min_char), ord(trans.output_type.max_char) + 1):
                                transformed_outputs.append(chr(char_code))
                        else:
                            transformed_outputs = [trans.output_type.to_string()]
                        
                        for transformed in transformed_outputs:
                            new_output = output_so_far + transformed
                            next_configurations.add((new_state, new_output))
                            
                            if len(next_configurations) > MAX_CONFIGURATIONS:
                                raise RuntimeError(f"FST transform explosion: too many configurations (>{MAX_CONFIGURATIONS})")
            
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
                        if isinstance(trans.output_type, SelfOutput):
                            # This shouldn't happen for epsilon transitions
                            empty_transitions.add((current_state, target_state))
                        elif isinstance(trans.output_type, FullRangeOutput):
                            # Full range output from epsilon transition
                            for char_code in range(ord(trans.output_type.min_char), ord(trans.output_type.max_char) + 1):
                                output_char = chr(char_code)
                                current_state.addTransition(Transition(output_char, output_char, target_state))
                        elif isinstance(trans.output_type, RangeOutput):
                            # One-to-one range output from epsilon transition
                            current_state.addTransition(Transition(trans.output_type.min_char, trans.output_type.max_char, target_state))
                        elif isinstance(trans.output_type, (LiteralOutput, VariableOutput)):
                            # Create transitions for the output string
                            output_str = trans.output_type.to_string()
                            temp_state = current_state
                            for i, c in enumerate(output_str):
                                if i == len(output_str) - 1:
                                    temp_state.addTransition(Transition(c, c, target_state))
                                else:
                                    next_state = State()
                                    temp_state.addTransition(Transition(c, c, next_state))
                                    temp_state = next_state
                        else:
                            # Create transitions for the output string
                            output_str = trans.output_type.to_string()
                            temp_state = current_state
                            for i, c in enumerate(output_str):
                                if i == len(output_str) - 1:
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
                
                # Handle range outputs directly
                #     # Full range mapping: create transitions for all characters in output range
                #         current_state.addTransition(Transition(output_char, output_char, target_state))
                if isinstance(trans.output_type, (SelfOutput, RangeOutput, FullRangeOutput)):
                    # One-to-one range mapping
                    # Use pattern matching for output range
                    if isinstance(trans.output_type, SelfOutput):
                        output_min, output_max = trans.min, trans.max
                    else:
                        output_min, output_max = trans.output_type.min_char, trans.output_type.max_char
                    #     output_min, output_max = trans.output_type.min_char, trans.output_type.max_char
                    current_state.addTransition(Transition(output_min, output_max, target_state))
                    continue
                
                if isinstance(trans.output_type, SelfOutput):
                    min_out, max_out = trans.min, trans.max
                elif isinstance(trans.output_type, LiteralOutput):
                    min_out = max_out = trans.output_type.value
                elif isinstance(trans.output_type, VariableOutput):
                    min_out = trans.output_type.template.replace("$self", trans.min)
                    max_out = trans.output_type.template.replace("$self", trans.max)
                else:
                    min_out = max_out = trans.output_type.to_string()
                
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

    def inverse(self) -> "FST":
        """Create the inverse FST by swapping input and output"""
        inversed_fst = FST()
        
        # Copy all states
        for state_id, state in self.states.items():
            inversed_fst.add_state(state_id, state.accept)
        
        # Set initial state
        if self.initial:
            inversed_fst.set_start(self.initial.id)
        
        # Keep track of temp state counter
        self._temp_state_counter = max(self.states.keys()) + 1000 if self.states else 1000
        
        # Process transitions
        for state in self.states.values():
            for trans in state.transitions:
                self._add_inversed_transition(inversed_fst, state.id, trans)
        
        return inversed_fst

    def _get_temp_state_id(self) -> int:
        """Get a unique temporary state ID"""
        temp_id = self._temp_state_counter
        self._temp_state_counter += 1
        return temp_id

    def _add_inversed_transition(self, inversed_fst: "FST", from_state_id: int, trans: "FST_Transition") -> None:
        """Add inversed transition to the FST"""
        
        # Handle epsilon transitions
        if trans.is_epsilon:
            if trans.output == "":
                # epsilon -> epsilon (no change)
                inversed_fst.add_transition(from_state_id, "$epsilon", None, "", trans.to.id, trans.is_not_consumed, True)
            else:
                # epsilon with output -> string input with empty output
                if isinstance(trans.output_type, FullRangeOutput):
                    # Full range output: each output char becomes separate input transition
                    for char_code in range(ord(trans.output_type.min_char), ord(trans.output_type.max_char) + 1):
                        output_char = chr(char_code)
                        inversed_fst.add_transition(from_state_id, output_char, output_char, "", trans.to.id, trans.is_not_consumed)
                elif isinstance(trans.output_type, RangeOutput):
                    # Range output: each output char becomes separate input transition  
                    for char_code in range(ord(trans.output_type.min_char), ord(trans.output_type.max_char) + 1):
                        output_char = chr(char_code)
                        inversed_fst.add_transition(from_state_id, output_char, output_char, "", trans.to.id, trans.is_not_consumed)
                elif isinstance(trans.output_type, VariableOutput):
                    # Variable output from epsilon doesn't make sense - $self undefined
                    raise ValueError("VariableOutput from epsilon transition is invalid - $self is undefined")
                elif isinstance(trans.output_type, (LiteralOutput, SelfOutput)):
                    # Literal output becomes string input
                    self._add_string_input_transition(inversed_fst, from_state_id, trans.output_type.to_string(), "", trans.to.id)
                else:
                    raise ValueError(f"Unsupported output type for epsilon transition: {type(trans.output_type)}")
            return
        
        # Handle regular transitions
        if trans.min is None or trans.max is None:
            # Skip invalid transitions
            return
        
        # Case 1: Empty output -> epsilon transition with input as output (should be full mapping)
        if trans.output == "":
            if trans.min == trans.max:
                inversed_fst.add_transition(from_state_id, "$epsilon", None, trans.min, trans.to.id, trans.is_not_consumed, True)
            else:
                # Range input becomes full range output in epsilon transition
                full_range_output = FullRangeOutput(trans.min, trans.max)
                inversed_fst.add_transition(from_state_id, "$epsilon", None, full_range_output.to_string(), trans.to.id, trans.is_not_consumed, True)
            return
        
        # Case 2: Single character input
        if trans.min == trans.max:
            input_char = trans.min
            
            if isinstance(trans.output_type, SelfOutput):
                # Single char -> single char (identity)
                inversed_fst.add_transition(from_state_id, input_char, input_char, input_char, trans.to.id, trans.is_not_consumed)
            elif isinstance(trans.output_type, FullRangeOutput):
                # Single char -> full range: create transitions for each character in range
                for char_code in range(ord(trans.output_type.min_char), ord(trans.output_type.max_char) + 1):
                    output_char = chr(char_code)
                    inversed_fst.add_transition(from_state_id, output_char, output_char, input_char, trans.to.id, trans.is_not_consumed)
            elif isinstance(trans.output_type, RangeOutput):
                # Single char -> range output: each output char maps to this single input char
                for char_code in range(ord(trans.output_type.min_char), ord(trans.output_type.max_char) + 1):
                    output_char = chr(char_code)
                    inversed_fst.add_transition(from_state_id, output_char, output_char, input_char, trans.to.id, trans.is_not_consumed)
            elif isinstance(trans.output_type, LiteralOutput) and len(trans.output_type.value) == 1:
                # Single char -> single char
                inversed_fst.add_transition(from_state_id, trans.output_type.value, trans.output_type.value, input_char, trans.to.id, trans.is_not_consumed)
            elif isinstance(trans.output_type, LiteralOutput) and len(trans.output_type.value) > 1:
                # Single char -> multi-char string: need to create intermediate states
                self._add_string_input_transition(inversed_fst, from_state_id, trans.output_type.value, input_char, trans.to.id)
            elif isinstance(trans.output_type, VariableOutput):
                # Single char -> variable template: calculate actual output and create intermediate states
                actual_output = trans.output_type.template.replace("$self", input_char)
                self._add_string_input_transition(inversed_fst, from_state_id, actual_output, input_char, trans.to.id)
            else:
                raise ValueError(f"Unsupported output type for single char input: {type(trans.output_type)}")
            return
        
        # Case 3: Range input
        if isinstance(trans.output_type, SelfOutput):
            # Range -> same range (identity)
            inversed_fst.add_transition(from_state_id, trans.min, trans.max, "$self", trans.to.id, trans.is_not_consumed)
        elif isinstance(trans.output_type, FullRangeOutput):
            # Range input -> full range output: each input char maps to entire output range
            for input_char_code in range(ord(trans.min), ord(trans.max) + 1):
                input_char = chr(input_char_code)
                # Each input character maps to the entire output range
                full_range_output = FullRangeOutput(trans.output_type.min_char, trans.output_type.max_char)
                inversed_fst.add_transition(from_state_id, "$epsilon", None, full_range_output.to_string(), trans.to.id, trans.is_not_consumed, True)
                # NOTE: This creates many epsilon transitions with range output
                # In the reverse direction, the entire output range maps to this single input char
                for output_char_code in range(ord(trans.output_type.min_char), ord(trans.output_type.max_char) + 1):
                    output_char = chr(output_char_code)
                    inversed_fst.add_transition(from_state_id, output_char, output_char, input_char, trans.to.id, trans.is_not_consumed)
        elif isinstance(trans.output_type, RangeOutput):
            # Range -> range: handle clamping properly  
            try:
                # Calculate range sizes
                input_range_size = ord(trans.max) - ord(trans.min) + 1
                output_range_size = ord(trans.output_type.max_char) - ord(trans.output_type.min_char) + 1
                
                if input_range_size == output_range_size:
                    # Compatible ranges, can swap directly (no clamping)
                    one_to_one_input_range = RangeOutput(trans.min, trans.max)
                    inversed_fst.add_transition(from_state_id, trans.output_type.min_char, trans.output_type.max_char, one_to_one_input_range.to_string(), trans.to.id, trans.is_not_consumed)
                else:
                    # Clamping detected: output range is smaller than input range
                    if input_range_size > output_range_size:
                        # For example: a--z (26) to A--F (6)
                        # a,b,c,d,e map one-to-one to A,B,C,D,E  
                        # f,g,h,...,z all map to F (clamped)
                        
                        # Create one-to-one mapping for non-clamped part
                        if output_range_size > 1:
                            # A--E maps to a--e (one-to-one)
                            one_to_one_output_max = chr(ord(trans.output_type.max_char) - 1)
                            one_to_one_input_max = chr(ord(trans.min) + output_range_size - 2)
                            one_to_one_range = RangeOutput(trans.min, one_to_one_input_max)
                            inversed_fst.add_transition(from_state_id, trans.output_type.min_char, one_to_one_output_max, one_to_one_range.to_string(), trans.to.id, trans.is_not_consumed)
                        
                        # F maps to *f--z (full range for all clamped inputs)
                        clamped_input_min = chr(ord(trans.min) + output_range_size - 1)
                        full_range_clamped = FullRangeOutput(clamped_input_min, trans.max)
                        inversed_fst.add_transition(from_state_id, trans.output_type.max_char, trans.output_type.max_char, full_range_clamped.to_string(), trans.to.id, trans.is_not_consumed)
                    else:
                        # Input range smaller than output range - expand to individual transitions
                        self._add_range_to_range_transitions(inversed_fst, from_state_id, trans.min, trans.max, trans.output_type.min_char, trans.output_type.max_char, trans.to.id)
            except (ValueError, IndexError):
                # Invalid range format - expand
                # self._add_range_to_string_transitions(inversed_fst, from_state_id, trans.min, trans.max, trans.output_type.to_string(), trans.to.id)
                raise ValueError(f"Invalid range format: {trans.min}--{trans.max}")
        elif isinstance(trans.output_type, LiteralOutput) and len(trans.output_type.value) == 1:
            # Range input -> single char output: create single char input with full range output
            full_range_output = FullRangeOutput(trans.min, trans.max)
            inversed_fst.add_transition(from_state_id, trans.output_type.value, trans.output_type.value, full_range_output.to_string(), trans.to.id, trans.is_not_consumed)
        elif isinstance(trans.output_type, LiteralOutput) and len(trans.output_type.value) > 1:
            # Range input -> multi-char string output: expand to individual transitions
            self._add_range_to_string_transitions(inversed_fst, from_state_id, trans.min, trans.max, trans.output_type.value, trans.to.id)
        elif isinstance(trans.output_type, VariableOutput):
            # Range input -> variable template output: expand each input char individually
            for input_char_code in range(ord(trans.min), ord(trans.max) + 1):
                input_char = chr(input_char_code)
                actual_output = trans.output_type.template.replace("$self", input_char)
                self._add_string_input_transition(inversed_fst, from_state_id, actual_output, input_char, trans.to.id)
        else:
            raise ValueError(f"Unsupported output type for range input: {type(trans.output_type)}")

    def _add_string_input_transition(self, reversed_fst: "FST", from_state_id: int, input_string: str, output: str, final_state_id: int) -> None:
        """Add transitions for string input by creating intermediate states"""
        if len(input_string) == 0:
            # Empty string input -> epsilon transition
            reversed_fst.add_transition(from_state_id, "$epsilon", None, output, final_state_id, False, True)
            return
        
        if len(input_string) == 1:
            # Single character
            reversed_fst.add_transition(from_state_id, input_string, input_string, output, final_state_id)
            return
        
        # Multiple characters: create intermediate states
        current_state = from_state_id
        for i, char in enumerate(input_string):
            if i == len(input_string) - 1:
                # Last character: output the final output
                reversed_fst.add_transition(current_state, char, char, output, final_state_id)
            else:
                # Intermediate character: empty output, move to temp state
                temp_state_id = self._get_temp_state_id()
                reversed_fst.add_state(temp_state_id)
                reversed_fst.add_transition(current_state, char, char, "", temp_state_id)
                current_state = temp_state_id

    def _add_range_to_string_transitions(self, reversed_fst: "FST", from_state_id: int, min_char: str, max_char: str, output: str, final_state_id: int) -> None:
        """Add many transitions for range input to string output"""
        for char_code in range(ord(min_char), ord(max_char) + 1):  # Expand all characters in the range
            char = chr(char_code)
            if output == "$self":
                # This case should not reach here, but handle it anyway
                reversed_fst.add_transition(from_state_id, char, char, char, final_state_id)
            elif len(output) == 1:
                # Range to single char
                reversed_fst.add_transition(from_state_id, output, output, char, final_state_id)
            else:
                # Range to string: create string input transition
                self._add_string_input_transition(reversed_fst, from_state_id, output, char, final_state_id)

    def _add_range_to_range_transitions(self, reversed_fst: "FST", from_state_id: int, input_min: str, input_max: str, output_min: str, output_max: str, final_state_id: int) -> None:
        """Add individual transitions for incompatible range-to-range mappings"""
        input_range_size = ord(input_max) - ord(input_min) + 1
        output_range_size = ord(output_max) - ord(output_min) + 1
        
        for i in range(max(input_range_size, output_range_size)):
            # Calculate input and output characters
            if i < input_range_size:
                input_char = chr(ord(input_min) + i)
            else:
                input_char = input_max  # Use last character if input range is smaller
                
            if i < output_range_size:
                output_char = chr(ord(output_min) + i)
            else:
                output_char = output_max  # Use last character if output range is smaller
            
            # Create reverse transition: output_char -> input_char
            reversed_fst.add_transition(from_state_id, output_char, output_char, input_char, final_state_id)

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

def compute_fst_automaton_product(fst: FST, automaton: Automaton) -> FST:
    if not CONFIG.get("enable_FST", True):
        raise ToolError("FST is disabled")
    
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
    return product_fst

def product_fst_automaton_with_projection(fst: FST, automaton: Automaton) -> Automaton:
    if not CONFIG.get("enable_FST", True):
        return RegExp(".*").toAutomaton()
    product_fst = compute_fst_automaton_product(fst, automaton)
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
                
                # Add epsilon transition output
                if t_fst.output:
                    if isinstance(t_fst.output_type, FullRangeOutput):
                        # Full range output from epsilon transition
                        for char_code in range(ord(t_fst.output_type.min_char), ord(t_fst.output_type.max_char) + 1):
                            output_char = chr(char_code)
                            s_product.addTransition(Transition(output_char, output_char, s_epsilon))
                    elif isinstance(t_fst.output_type, RangeOutput):
                        # One-to-one range output from epsilon transition
                        s_product.addTransition(Transition(t_fst.output_type.min_char, t_fst.output_type.max_char, s_epsilon))
                    elif isinstance(t_fst.output_type, LiteralOutput):
                        # Create transitions for the literal output string
                        output_str = t_fst.output_type.value
                        current_state = s_product
                        for i, c in enumerate(output_str):
                            if i == len(output_str) - 1:
                                current_state.addTransition(Transition(c, c, s_epsilon))
                            else:
                                next_state = State()
                                current_state.addTransition(Transition(c, c, next_state))
                                current_state = next_state
                    elif isinstance(t_fst.output_type, SelfOutput):
                        # SelfOutput from epsilon transition is invalid - no input context
                        raise ValueError("SelfOutput from epsilon transition is invalid - no input context")
                    elif isinstance(t_fst.output_type, VariableOutput):
                        # VariableOutput from epsilon transition is invalid - $self undefined
                        raise ValueError("VariableOutput from epsilon transition is invalid - $self is undefined")
                    else:
                        raise ValueError(f"Unsupported output type for epsilon transition: {type(t_fst.output_type)}")
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
                        
                        # Handle range outputs directly
                        if isinstance(t_fst.output_type, FullRangeOutput):
                            # Full range mapping: create transitions for all characters in output range
                            for char_code in range(ord(t_fst.output_type.min_char), ord(t_fst.output_type.max_char) + 1):
                                output_char = chr(char_code)
                                s_product.addTransition(Transition(output_char, output_char, s))
                        elif isinstance(t_fst.output_type, (SelfOutput, RangeOutput)):
                            # One-to-one range mapping
                            # Use pattern matching for output range
                            if isinstance(t_fst.output_type, SelfOutput):
                                # For SelfOutput, use the intersection range, not the full FST range
                                output_min, output_max = min_in, max_in
                            elif isinstance(t_fst.output_type, RangeOutput):
                                # For RangeOutput, calculate the corresponding output range based on intersection
                                input_offset_min = ord(min_in) - ord(t_fst.min)
                                input_offset_max = ord(max_in) - ord(t_fst.min)
                                output_char_min = chr(ord(t_fst.output_type.min_char) + input_offset_min)
                                output_char_max = chr(ord(t_fst.output_type.min_char) + input_offset_max)
                                # Clamp to max if needed
                                output_min = chr(min(ord(output_char_min), ord(t_fst.output_type.max_char)))
                                output_max = chr(min(ord(output_char_max), ord(t_fst.output_type.max_char)))
                            else:
                                output_min = output_max = t_fst.output_type.to_string()
                            s_product.addTransition(Transition(output_min, output_max, s))
                        else:
                            # Use pattern matching for transform behavior
                            if isinstance(t_fst.output_type, SelfOutput):
                                min_out, max_out = min_in, max_in
                            elif isinstance(t_fst.output_type, LiteralOutput):
                                min_out = max_out = t_fst.output_type.value
                            elif isinstance(t_fst.output_type, VariableOutput):
                                min_out = t_fst.output_type.template.replace("$self", min_in)
                                max_out = t_fst.output_type.template.replace("$self", max_in)
                            elif isinstance(t_fst.output_type, RangeOutput):
                                # Calculate offset from input range start
                                min_input_offset = ord(min_in) - ord(t_fst.min)
                                max_input_offset = ord(max_in) - ord(t_fst.min)
                                min_output_char = chr(ord(t_fst.output_type.min_char) + min_input_offset)
                                max_output_char = chr(ord(t_fst.output_type.min_char) + max_input_offset)
                                # Clamp to max if needed
                                min_out = chr(min(ord(min_output_char), ord(t_fst.output_type.max_char)))
                                max_out = chr(min(ord(max_output_char), ord(t_fst.output_type.max_char)))
                            else:
                                raise ValueError(f"Unsupported output type for regular transition: {type(t_fst.output_type)}")
                            if len(min_out) == 0 or len(max_out) == 0:
                                if min_out != max_out:
                                    raise ValueError(f"Output range not supported: {min_out}--{max_out}")
                                empty_transitions.add((s_product, s))
                            elif len(min_out) > 1 or len(max_out) > 1:
                                # Handle variable outputs with $self
                                if isinstance(t_fst.output_type, VariableOutput):
                                    template = t_fst.output_type.template
                                    if not template.endswith("$self") and not template.startswith("$self"):
                                        raise ValueError(f"Output range not supported: {min_out}--{max_out}")
                                    if template.endswith("$self"):
                                        prefix = template[:-5]
                                        #     raise ValueError(f"Output range not supported: {min_out}--{max_out}")
                                        current_state = s_product
                                        for i, c in enumerate(prefix):
                                            s_1 = State()
                                            current_state.addTransition(Transition(c, c, s_1))
                                            current_state = s_1
                                        current_state.addTransition(Transition(min_in, max_in, s))
                                    elif template.startswith("$self"):
                                        suffix = template[5:]
                                        #     raise ValueError(f"Output range not supported: {min_out}--{max_out}")
                                        current_state = State()
                                        s_product.addTransition(Transition(min_in, max_in, current_state))
                                        for i, c in enumerate(suffix):
                                            if i != len(suffix) - 1:
                                                s_1 = State()
                                                current_state.addTransition(Transition(c, c, s_1))
                                                current_state = s_1
                                            else:
                                                current_state.addTransition(Transition(c, c, s))
                                else:
                                    # Literal multi-character output
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
    product = product_fst_automaton(fst, automaton)
    print(product)
    print(product.run("X"))
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
