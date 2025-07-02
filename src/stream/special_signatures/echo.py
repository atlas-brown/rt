import re
from stream.command_signature import CommandSignature, InferenceResult
from stream.regular_type import RegularType
from stream.tool_error import ToolError
from stream.user_annotation import AnnotationType
from stream.utils.logger import get_logger

class EchoSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        get_logger().get_latest_record()["command_list"][-1]["command_type_loses_precision"] = False
        self_contained = True
        operands = super().get_operands(parsed_command_invocation)
        if len(operands) == 0:
            raise ToolError("No operand provided for echo")
        
        original_operand = operands[0]
        
        # Find all variable matches and build pattern
        var_matches = list(re.finditer(r'(\$\{.*?\})', original_operand))
        
        if not var_matches:
            # No variables, just escape the whole string
            pattern = re.escape(original_operand)
        else:
            # Process in parts: escape literal parts, keep variable patterns unescaped
            pattern_parts = []
            last_end = 0
            
            for var_match in var_matches:
                # Add escaped literal part before this variable
                literal_part = original_operand[last_end:var_match.start()]
                if literal_part:
                    pattern_parts.append(re.escape(literal_part))
                
                # Add variable replacement (unescaped)
                var_name = var_match.group(1)
                replacement = "[^\n]*"  # Default pattern
                self_contained = False
                
                if var_name in env_annotations:
                    for annot in env_annotations[var_name]:
                        if annot.annotation_type == AnnotationType.VAR:
                            replacement = annot.pattern
                            break
                
                pattern_parts.append(replacement)
                last_end = var_match.end()
            
            # Add escaped literal part after the last variable
            remaining_literal = original_operand[last_end:]
            if remaining_literal:
                pattern_parts.append(re.escape(remaining_literal))
            
            pattern = ''.join(pattern_parts)

        flags = set(map(lambda flag_option: flag_option.get_name(), parsed_command_invocation.flag_option_list))
        if "-n" not in flags:
            pattern = pattern + "\n"
        get_logger().get_latest_record()["command_list"][-1]["output_type"] = pattern
        return InferenceResult(RegularType(pattern, repr_mode="stream", tainted=False), self_contained=self_contained)
        
