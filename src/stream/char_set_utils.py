import re

from stream.tool_error import ToolError


def preprocess_char_set(source_chars: str) -> str:
    """
    source_chars: C
    C: CC | c | POSIX character class | c-c

    return: C'
    C': c | C'C'
    """
    source_chars = replace_POSIX_class(source_chars)
    processed_chars = ""
    contains_dash = False
    i = 0
    if source_chars and source_chars[0] == '-':
        processed_chars += '-'
        i = 1

    while i < len(source_chars):
        if source_chars[i] == '-' and i > 0 and i < len(source_chars) - 1:
            start = source_chars[i-1]
            end = source_chars[i+1]
            if ord(start) > ord(end):
                raise ToolError(f"invalid range: {start}-{end}")
            else:
                for char_code in range(ord(start), ord(end) + 1):
                    if chr(char_code) == '-':
                        contains_dash = True
                    else:
                        processed_chars += chr(char_code)
            i += 1
        elif source_chars[i] == '-' and i == len(source_chars) - 1:
            contains_dash = True
        else:
            processed_chars += source_chars[i]
        i += 1

    if contains_dash:
        processed_chars += '-'

    processed_chars = process_escape_chars(processed_chars)
    return processed_chars


def replace_POSIX_class(source_chars: str) -> str:
    source_chars = source_chars.replace("[:lower:]", "a-z")
    source_chars = source_chars.replace("[:upper:]", "A-Z")
    source_chars = source_chars.replace("[:alpha:]", "a-zA-Z")
    source_chars = source_chars.replace("[:punct:]", "!-/:-@[-`{-~")
    source_chars = source_chars.replace("[:digit:]", "0-9")
    source_chars = source_chars.replace("[:alnum:]", "a-zA-Z0-9")
    source_chars = source_chars.replace("[:blank:]", " \t")
    source_chars = source_chars.replace("[:word:]", "a-zA-Z0-9_")
    source_chars = source_chars.replace("[:xdigit:]", "0-9a-fA-F")
    source_chars = source_chars.replace("[:space:]", " \t\n\r\f\v")
    return source_chars


def process_escape_chars(source_chars: str) -> str:
    source_chars = source_chars.replace("\\\\", "\\")
    escape_dict = {
        'n': '\n',
        't': '\t',
        'r': '\r',
        'v': '\v',
        'f': '\f',
        'b': '\b',
        's': ' ',
        '+': '+',
        '{': '{',
        '}': '}',
        '|': '|',
        '&': '&',
        '~': '~',
        '*': '*',
        '?': '?',
        '.': '.',
        '^': '^',
        '$': '$',
        '(': '(',
        ')': ')',
        '[': '[',
        ']': ']',
        '"': '"',
        "'": "'",
        '-': '-',
        '\\': '\\'
    }
    source_chars = re.sub(r'\\([\\ntrvfbs+{}|&~*?.^$()[\]"\']|-)', lambda m: escape_dict[m.group(1)], source_chars)
    return source_chars


def complement_set(source_chars: str) -> str:
    result = ""
    for i in range(256):
        if chr(i) not in source_chars:
            result += chr(i)
    if result == "":
        raise ToolError("Invalid set for tr (empty complement)")
    return result
