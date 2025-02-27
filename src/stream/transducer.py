from collections import deque
import jpype
import jpype.imports
if not jpype.isJVMStarted():
    jpype.startJVM(classpath=["jars/automaton.jar"])
from dk.brics.automaton import Automaton, RegExp, State, Transition # type: ignore
from stream.tool_error import ToolError

from typing import Deque, List, Callable, Optional, Dict, Set, Tuple

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
    def __init__(self, min: Optional[str], max: Optional[str], output_func: Callable[[str], str], to: FST_State, is_other: bool = False) -> None:
        self.min: Optional[str] = min
        self.max: Optional[str] = max
        self.output_func: Callable[[str], str] = output_func
        self.to: FST_State = to
        self.is_other: bool = is_other

    def applies(self, c: str) -> bool:
        if self.min is None or self.max is None:
            return False
        return ord(self.min) <= ord(c) <= ord(self.max)

    def transform(self, c: str) -> str:
        return self.output_func(c)
    
    def __repr__(self) -> str:
        return f"FST_Transition(min={ord(self.min)}, max={ord(self.max)}, to={self.to.id})"

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

    def add_transition(self, from_state_id: int, min_in: str, max_in: Optional[str], output: str, next_state_id: int) -> None:
        from_state = self.add_state(from_state_id)
        next_state = self.add_state(next_state_id)
        if min_in == "other":
            is_other = True
            start_val, end_val = None, None
        else:
            is_other = False
            start_val, end_val = min_in, max_in
        if output == "self":
            output_func: Callable[[str], str] = lambda c: c
        elif "-" in output:
            parts = output.split("-")
            if len(parts) != 2:
                raise ToolError(f"Invalid transition output: {output}")
            min_out, max_out = parts[0], parts[1]
            if ord(min_out) > ord(max_out):
                raise ToolError(f"Invalid transition output: {output}")
            output_func = lambda c, min_in=min_in, min_out=min_out, max_out=max_out: chr(min(ord(min_out) + ord(c) - ord(min_in), ord(max_out)))
        else:
            output_func = lambda c, o=output: o
        trans = FST_Transition(start_val, end_val, output_func, to=next_state, is_other=is_other)
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

    def _compute_complement_intervals(self, intervals: List[Tuple[int, int]], min_val: int = 0, max_val: int = 0x10FFFF) -> List[Tuple[int, int]]:
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
                    new_trans = FST_Transition(new_min, new_max, other.output_func, to=other.to, is_other=False)
                    state.add_transition(new_trans)
            state.transitions = [t for t in state.transitions if not t.is_other]

    def transform_all(self, input_string: str) -> Set[str]:
        if self.initial is None:
            return set()
        configurations: Set[Tuple[FST_State, str]] = {(self.initial, "")}
        for c in input_string:
            next_configurations: Set[Tuple[FST_State, str]] = set()
            for state, output_so_far in configurations:
                for trans in state.transitions:
                    if trans.applies(c):
                        new_state = trans.to
                        new_output = output_so_far + trans.transform(c)
                        next_configurations.add((new_state, new_output))
            configurations = next_configurations
        results: Set[str] = {out for state, out in configurations if state.accept}
        return results
    
    def __repr__(self) -> str:
        return "\n".join(f"{state_id}: {state}" for state_id, state in self.states.items())

def create_fst(transition_specs: List[Tuple[int, str, str, int]], start_state: int = 0, final_states: Optional[Set[int]] = None) -> FST:
    fst = FST()
    fst.set_start(start_state)
    if final_states is None:
        final_states = {start_state}
    for spec in transition_specs:
        from_state, input_range, output, next_state = spec
        if input_range == "other":
            fst.add_transition(from_state, "other", None, output, next_state)
        else:
            if '--' in input_range:
                parts = input_range.split('--')
                if len(parts) != 2:
                    raise ToolError(f"Invalid input range format: {input_range}")
                min_in, max_in = parts[0], parts[1]
            else:
                min_in = input_range
                max_in = input_range
            fst.add_transition(from_state, min_in, max_in, output, next_state)
    for fs in final_states:
        fst.set_accept(fs)
    fst._process_other_transitions()
    return fst


def product_fst_automaton(fst: FST, automaton: Automaton) -> Automaton:
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
            for t_automaton in transitions_automaton:
                if ord(t_automaton.getMax()) >= ord(t_fst.min) and ord(t_automaton.getMin()) <= ord(t_fst.max):
                    p = (t_fst.to, t_automaton.getDest())
                    if p not in new_states:
                        s = State()
                        new_states[p] = s
                        worklist.append(p)
                    s = new_states[p]
                    min = t_fst.min if ord(t_fst.min) > ord(t_automaton.getMin()) else t_automaton.getMin()
                    max = t_fst.max if ord(t_fst.max) < ord(t_automaton.getMax()) else t_automaton.getMax()
                    min_out = t_fst.output_func(min)
                    max_out = t_fst.output_func(max)
                    if len(min_out) == 0 or len(max_out) == 0:
                        if min_out != max_out:
                            raise ToolError(f"Output range not supported: {min_out}-{max_out}")
                        empty_transitions.add((s_product, s))
                    elif len(min_out) > 1 or len(max_out) > 1:
                        if min_out != max_out:
                            raise ToolError(f"Output range not supported: {min_out}-{max_out}")
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

    # handle empty transitions
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
    product.setDeterministic(False)
    product.removeDeadTransitions()
    product.minimize()
    return product

def full_stream_to_line_based_FST() -> FST:
    specs = [
        (0, "\n", "", 100),
        (0, "other", "self", 1),
        (0, "other", "", 2),
        (1, "\n", "", 100),
        (1, "other", "self", 1),
        (2, "\n", "", 0),
        (2, "other", "", 2),
        (100, "other", "", 100),
    ]
    return create_fst(specs, start_state=0, final_states={100})


def translation_FST(set1: str, set2: str) -> FST:
    specs = []
    for i, c in enumerate(set1):
        if i < len(set2):
            c2 = set2[i]
        else:
            c2 = set2[-1]
        specs.append((0, c, c2, 0))
    specs.append((0, "other", "self", 0))
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
        specs.append((i, "other", "self", 0))
    return create_fst(specs, start_state=0, final_states=final_states)


def delete_FST(set1: str) -> FST:
    specs = []
    for c in set1:
        specs.append((0, c, "", 0))
    specs.append((0, "other", "self", 0))
    return create_fst(specs, start_state=0, final_states={0})

def cut_FST(delimiter: str, fields: List[int]) -> FST:
    # cut -f 1 -> [1]
    # cut -f 1,3 -> [1, 3]
    # cut -f 1-3 -> [1, 2, 3]
    specs = []
    max_field = max(fields)
    for i in range(1, max_field + 1):
        if i in fields and i != max_field:
            specs.append((i, delimiter, delimiter, i + 1))
        else:
            specs.append((i, delimiter, "", i + 1))
        
        if i in fields:
            specs.append((i, "other", "self", i))
        else:
            specs.append((i, "other", "", i))

    specs.append((max_field + 1, "other", "", max_field + 1))
    return create_fst(specs, start_state=1, final_states={i for i in range(1, max_field + 2)})
        


        



    

    

if __name__ == '__main__':
    # specs = [
    #     (0, "a-z", "self", 0),
    #     (0, "a-z", "+", 0),
    #     (0, "A-Z", "self", 0),
    #     (0, "A-Z", "+", 0),
    #     (0, "0-9", "self", 0),
    #     (0, "other", "-", 0)
    # ]
    # fst = create_fst(specs, start_state=0, final_states={0})
    # test_str = "Hello123 世界"
    # try:
    #     result = fst.transform_all(test_str)
    #     print("output:", result)
    # except Exception as e:
    #     print("Transformation failed:", e)


    regex = RegExp("[P-Z]+[a-z][0-9]+")
    automaton = regex.toAutomaton()
    specs = [
        (0, "a--z", "A--Z", 0),
        (0, 'A--Z', '0--9', 0),
        (0, "other", "self", 0),
        (0, "other", "a", 0),
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

	# static public Automaton intersection(Automaton a1, Automaton a2) {
	# 	if (a1.isSingleton()) {
	# 		if (a2.run(a1.singleton))
	# 			return a1.cloneIfRequired();
	# 		else
	# 			return BasicAutomata.makeEmpty();
	# 	}
	# 	if (a2.isSingleton()) {
	# 		if (a1.run(a2.singleton))
	# 			return a2.cloneIfRequired();
	# 		else
	# 			return BasicAutomata.makeEmpty();
	# 	}
	# 	if (a1 == a2)
	# 		return a1.cloneIfRequired();
	# 	Transition[][] transitions1 = Automaton.getSortedTransitions(a1.getStates());
	# 	Transition[][] transitions2 = Automaton.getSortedTransitions(a2.getStates());
	# 	Automaton c = new Automaton();
	# 	LinkedList<StatePair> worklist = new LinkedList<StatePair>();
	# 	HashMap<StatePair, StatePair> newstates = new HashMap<StatePair, StatePair>();
	# 	StatePair p = new StatePair(c.initial, a1.initial, a2.initial);
	# 	worklist.add(p);
	# 	newstates.put(p, p);
	# 	while (worklist.size() > 0) {
	# 		p = worklist.removeFirst();
	# 		p.s.accept = p.s1.accept && p.s2.accept;
	# 		Transition[] t1 = transitions1[p.s1.number];
	# 		Transition[] t2 = transitions2[p.s2.number];
	# 		for (int n1 = 0, b2 = 0; n1 < t1.length; n1++) {
	# 			while (b2 < t2.length && t2[b2].max < t1[n1].min)
	# 				b2++;
	# 			for (int n2 = b2; n2 < t2.length && t1[n1].max >= t2[n2].min; n2++) 
	# 				if (t2[n2].max >= t1[n1].min) {
	# 					StatePair q = new StatePair(t1[n1].to, t2[n2].to);
	# 					StatePair r = newstates.get(q);
	# 					if (r == null) {
	# 						q.s = new State();
	# 						worklist.add(q);
	# 						newstates.put(q, q);
	# 						r = q;
	# 					}
	# 					char min = t1[n1].min > t2[n2].min ? t1[n1].min : t2[n2].min;
	# 					char max = t1[n1].max < t2[n2].max ? t1[n1].max : t2[n2].max;
	# 					p.s.transitions.add(new Transition(min, max, r.s));
	# 				}
	# 		}
	# 	}
	# 	c.deterministic = a1.deterministic && a2.deterministic;
	# 	c.removeDeadTransitions();
	# 	c.checkMinimizeAlways();
	# 	return c;
	# }
