from command_signature import CommandSignature
from pash_annotations.datatypes.BasicDatatypes import Operand

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
            for i, arg in enumerate(flag_args["-e"]):
                if i > 0:
                    pattern += "|"
                pattern += arg
            parsed_command_invocation.operand_list.append(Operand(pattern))
            
        return super().output_type_inference(previous_output_type, parsed_command_invocation)
        
