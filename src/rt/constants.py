from rt.java_api import RegExp
from pathlib import Path

ALPHABET_SIZE = 256  # ASCII range
ALPHABET_AUTOMATON = RegExp(f"[{chr(0)}-{chr(ALPHABET_SIZE - 1)}]*").toAutomaton()
NO_NEWLINE_AUTOMATON = RegExp("[^\\n]*").toAutomaton()
EXTRA_PASH_ANNOTATIONS_DIR = Path(__file__).resolve().parent / "shell" / "pash_annotations"
