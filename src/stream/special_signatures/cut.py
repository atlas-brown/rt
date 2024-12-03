import re
from command_signature import CommandSignature
from stream.regular_type import RegularType
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

class CutSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_input_type(self, parsed_command_invocation) -> RegularType:
        flags = set()
        flag_args = {}
        for flag in parsed_command_invocation.flag_option_list:
            name = flag.get_name()
            flags.add(name)
            if hasattr(flag, 'get_arg') and flag.get_arg():
                flag_args[name] = flag.get_arg()

        delimiter = "(\s+)"
        if '-d' in flags:
            delimiter = f"({flag_args['-d']}+)"

        if '-f' in flags:
            field_num = int(flag_args.get('-f', '1'))
            
            if field_num <= 1:
                return RegularType(".*")
            
            pattern = f".*({delimiter}.*){{{field_num-1}}}"
            return RegularType(pattern)
            
        return super().get_input_type(parsed_command_invocation)

    def output_type_inference(self, previous_output_type: RegularType, parsed_command_invocation: CommandInvocationInitial) -> RegularType:
        return super().output_type_inference(previous_output_type, parsed_command_invocation)
        # if '-f' in flags:
        #     field_num = int(flag_args.get('-f', '1'))
        #     pattern = previous_output_type.pattern
            
        #     field_patterns = re.split(delimiter, pattern)
        #     if field_num <= len(field_patterns):
        #         return RegularType(field_patterns[field_num - 1])
        #     raise ValueError(f"when cutting by field number, the field number must be less than or equal to the number of fields in the input: {field_num} > {len(field_patterns)}")
            
        # return super().inference_output_type(previous_output_type, parsed_command_node)