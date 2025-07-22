from stream.transducer_utils import *

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