from stream.transducer_utils import *

def _clone_automaton_from_state(automaton: Automaton, initial_state: State) -> Automaton:
    state_mapping: Dict[State, State] = {}
    for state in automaton.getStates():
        cloned_state = State()
        cloned_state.setAccept(state.isAccept())
        state_mapping[state] = cloned_state

    for state, cloned_state in state_mapping.items():
        for transition in state.getTransitions():
            cloned_state.addTransition(
                Transition(
                    transition.getMin(),
                    transition.getMax(),
                    state_mapping[transition.getDest()],
                )
            )

    cloned_automaton = Automaton()
    cloned_automaton.setInitialState(state_mapping[initial_state])
    cloned_automaton.setDeterministic(automaton.isDeterministic())
    return cloned_automaton


def _intersect_ranges(
    left_min: int,
    left_max: int,
    right_min: int,
    right_max: int,
) -> Optional[Tuple[int, int]]:
    min_value = max(left_min, right_min)
    max_value = min(left_max, right_max)
    if min_value > max_value:
        return None
    return min_value, max_value


def _complement_ranges(
    ranges: List[Tuple[int, int]],
    min_value: int,
    max_value: int,
) -> List[Tuple[int, int]]:
    if min_value > max_value:
        return []
    if not ranges:
        return [(min_value, max_value)]

    merged: List[Tuple[int, int]] = []
    for start, end in sorted(ranges):
        if end < min_value or start > max_value:
            continue
        start = max(start, min_value)
        end = min(end, max_value)
        if not merged or start > merged[-1][1] + 1:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))

    complement: List[Tuple[int, int]] = []
    cursor = min_value
    for start, end in merged:
        if cursor < start:
            complement.append((cursor, start - 1))
        cursor = end + 1
    if cursor <= max_value:
        complement.append((cursor, max_value))
    return complement


def _add_guarded_fallbacks(
    fst: FST,
    automaton: Automaton,
    state_map: Dict[State, int],
    guarded_fallbacks: List[Tuple[int, str, str, int]],
    restart_state_id: int,
    abort_state_id: int,
) -> None:
    if not guarded_fallbacks:
        return

    base_state_ids = list(fst.states)
    min_base_state_id = min(base_state_ids)
    state_span = max(base_state_ids) - min_base_state_id + 1
    first_guarded_state_id = max(base_state_ids) + 1
    id_to_state = {state_id: state for state, state_id in state_map.items()}

    def guarded_state_id(base_state_id: int, guard_state_id: int) -> int:
        return first_guarded_state_id + guard_state_id * state_span + (base_state_id - min_base_state_id)

    for guard_state_id, guard_state in id_to_state.items():
        if guard_state.isAccept():
            continue
        for base_state_id in base_state_ids:
            base_state = fst.states[base_state_id]
            fst.add_state(
                guarded_state_id(base_state_id, guard_state_id),
                accept=base_state.accept,
            )

    for guard_state_id, guard_state in id_to_state.items():
        if guard_state.isAccept():
            continue
        guard_transitions = list(guard_state.getSortedTransitions(True))
        for base_state_id in base_state_ids:
            base_state = fst.states[base_state_id]
            source_state_id = guarded_state_id(base_state_id, guard_state_id)
            for base_transition in base_state.transitions:
                if base_transition.min is None or base_transition.max is None:
                    continue
                base_min = ord(base_transition.min)
                base_max = ord(base_transition.max)
                guarded_ranges: List[Tuple[int, int]] = []

                for guard_transition in guard_transitions:
                    intersection = _intersect_ranges(
                        base_min,
                        base_max,
                        ord(guard_transition.getMin()),
                        ord(guard_transition.getMax()),
                    )
                    if intersection is None:
                        continue
                    transition_min, transition_max = intersection
                    guarded_ranges.append((transition_min, transition_max))
                    guard_dest_state_id = state_map[guard_transition.getDest()]
                    if guard_transition.getDest().isAccept():
                        target_state_id = abort_state_id
                    else:
                        target_state_id = guarded_state_id(
                            base_transition.to.id,
                            guard_dest_state_id,
                        )
                    fst.add_transition(
                        source_state_id,
                        chr(transition_min),
                        chr(transition_max),
                        base_transition.output,
                        target_state_id,
                    )

                for transition_min, transition_max in _complement_ranges(
                    guarded_ranges,
                    base_min,
                    base_max,
                ):
                    fst.add_transition(
                        source_state_id,
                        chr(transition_min),
                        chr(transition_max),
                        base_transition.output,
                        base_transition.to.id,
                    )

    restart_transitions = list(fst.states[restart_state_id].transitions)
    for source_state_id, fallback_min, fallback_max, guard_state_id in guarded_fallbacks:
        for restart_transition in restart_transitions:
            if restart_transition.min is None or restart_transition.max is None:
                continue
            intersection = _intersect_ranges(
                ord(fallback_min),
                ord(fallback_max),
                ord(restart_transition.min),
                ord(restart_transition.max),
            )
            if intersection is None:
                continue
            transition_min, transition_max = intersection
            fst.add_transition(
                source_state_id,
                chr(transition_min),
                chr(transition_max),
                restart_transition.output,
                guarded_state_id(restart_transition.to.id, guard_state_id),
            )



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
                a = _clone_automaton_from_state(automata, t.getDest())
                b = _clone_automaton_from_state(automata, trans.getDest())
                if not a.subsetOf(b):
                    intersentions.append((new_min, new_max))
        return intersentions




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
                a = _clone_automaton_from_state(automata, t.getDest())
                b = _clone_automaton_from_state(automata, trans.getDest())
                if not a.subsetOf(b):
                    intersentions.append((new_min, new_max))
        return intersentions

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
    state_map: Dict[State, int] = {}
    specs = []
    guarded_fallbacks: List[Tuple[int, str, str, int]] = []
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
                        guarded_fallbacks.append((state_id + num_states, new_min, new_max, dest_state_id))
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
        
    fst = create_fst(specs, start_state=new_initial_state, final_states=final_states)
    _add_guarded_fallbacks(fst, automaton, state_map, guarded_fallbacks, new_initial_state, abort_state)
    return fst


def start_regex_replacement_FST(automaton: Automaton, s2: str) -> FST:

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
                a = _clone_automaton_from_state(automata, t.getDest())
                b = _clone_automaton_from_state(automata, trans.getDest())
                if not a.subsetOf(b):
                    intersentions.append((new_min, new_max))
        return intersentions




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
