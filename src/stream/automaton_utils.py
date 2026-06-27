from typing import Set, Tuple

from stream.java_api import Automaton, State, Transition
from stream.transducer import process_empty_transitions


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
    process_empty_transitions(empty_transitions)
    out_nfa.setDeterministic(False)
    out_nfa.removeDeadTransitions()
    out_nfa.minimize()
    return out_nfa
