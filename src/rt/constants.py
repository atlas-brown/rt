from rt.java_api import RegExp

ALPHABET_SIZE = 256  # ASCII range
ALPHABET_AUTOMATON = RegExp(f"[{chr(0)}-{chr(ALPHABET_SIZE - 1)}]*").toAutomaton()
NO_NEWLINE_AUTOMATON = RegExp("[^\\n]*").toAutomaton()
