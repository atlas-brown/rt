from command_signature import CommandSignature
from pash_annotations.datatypes.BasicDatatypes import Operand

from stream.regular_type import RegularType

class GrepSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def output_type_inference(self, previous_output_type, parsed_command_invocation):
        flags = set()
        flag_args : dict[str, list[str]] = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, 'get_arg') and flag.get_arg():
                if name not in flag_args:
                    flag_args[name] = []
                flag_args[name].append(flag.get_arg())

        if "-e" in flags:
            pattern = ""
            arg_count = len(parsed_command_invocation.operand_list) + 1
            for i, arg in enumerate(flag_args["-e"]):
                if i > 0:
                    pattern += f"|({arg})"
                else:
                    pattern += f"({arg})"
        else:
            pattern = parsed_command_invocation.operand_list[0].name
            arg_count = len(parsed_command_invocation.operand_list)
        
        original_pattern = pattern

        if "-o" not in flags:
            # not completely correct, fix it later
            if not startsWithAtStart(pattern):
                pattern = ".*" + pattern
            if not endsWithAtEnd(pattern):
                pattern = pattern + ".*"
        
        pattern = remove_anchors(pattern)
        original_pattern = remove_anchors(original_pattern)
        
        if "-w" in flags:
            pattern = f"(({pattern}))&(((.*\\W)?){original_pattern}((\\W.*)?))"

        if "-v" in flags:
            pattern = f"(?!({pattern}))"

        if arg_count == 1:
            pattern = f"(({pattern}))&(({previous_output_type.pattern}))"

        return RegularType(pattern)
        
# temporary solution, need to be fixed
def startsWithAtStart(pattern: str) -> bool:
    while pattern.startswith("("):
        pattern = pattern[1:]
    if pattern.startswith("^"):
        return True
    return False

def endsWithAtEnd(pattern: str) -> bool:
    while pattern.endswith(")"):
        pattern = pattern[:-1]
    if pattern.endswith("$"):
        if len(pattern) == 1 or pattern[-2] != "\\":
            return True
    return False

def remove_anchors(pattern: str) -> str:
    if startsWithAtStart(pattern):
        first_caret_index = pattern.index('^')
        pattern = pattern[:first_caret_index] + pattern[first_caret_index + 1:]
    
    if endsWithAtEnd(pattern):
        last_dollar_index = pattern.rindex('$')
        pattern = pattern[:last_dollar_index] + pattern[last_dollar_index + 1:]
    
    return pattern