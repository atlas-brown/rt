import re


def char_set_complement(char_set: str, alphabet_start: int, alphabet_size: int) -> str:
    """Return the complement of a character set assuming the given alphabet."""

    complement = ""
    for i in range(alphabet_start, alphabet_start + alphabet_size):
        if chr(i) not in char_set:
            complement += chr(i)
    return complement


# NOTE: This function is only used in the stream module (stream/regular_type.py),
# not in the rt module. It is kept here for potential future use or external consumers.
def preprocess(pattern: str | None) -> str:
    """Preprocess a regex pattern by replacing shell-style expansions and lookahead.

    Replaces ``${var}`` and ``$(cmd)`` patterns with ``(.*)`` (match anything), and
    ``(?!...)`` (negative lookahead) with ``~(...)`` (complement syntax). Returns an
    empty string if None is passed.
    """
    if pattern is None:
        pattern = ""
    replace_pattern = r"\$\{[^}]*\}|\$\([^)]*\)|\\\$\\\{[^}]*\\\}|\\\$\\\([^)]*\\\)"
    pattern = re.sub(replace_pattern, r"(.*)", pattern)
    replace_pattern = r"\(\?!"
    pattern = re.sub(replace_pattern, r"~(", pattern)
    return pattern


# NOTE: This function is only used in the stream module (stream/transformations.py
# and stream/transformation_ast.py), not in the rt module. It is kept here for
# potential future use or external consumers.
def build_character_class(chars: str) -> str:
    escaped_chars = []
    seen = set()
    for ch in chars:
        if ch in seen:
            continue
        seen.add(ch)
        if ch == "\n":
            escaped = "\\n"
        elif ch == "\t":
            escaped = "\\t"
        elif ch == "\r":
            escaped = "\\r"
        elif ch == "\\":
            escaped = "\\\\"
        elif ch == "-":
            escaped = "\\-"
        elif ch == "]":
            escaped = "\\]"
        elif ch == "^":
            escaped = "\\^"
        else:
            escaped = re.escape(ch)
        escaped_chars.append(escaped)
    return "".join(escaped_chars)
