from stream.command_signature import CommandSignature, InferenceResult
from stream.regular_type import RegularType
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
import re


class FindSignature(CommandSignature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def output_type_inference(self, previous_output_type, parsed_command_invocation, env_annotations):
        # find keywords in parsed_command_invocation.operand_list, e.g., -exec will be "-e", "-x", "-e", "-c"  in order, keywords can be arbitrary
        # example operand_list: [/workspace, -t, -y, -p, -e, f, -s, -i, -z, -e, +1k, -e, -x, -e, -c, ls, -l, -s, {}, +]
        keywords = ["exec"]
        # if exec is found, extract the following command and its arguments, then instantiate a new CommandInvocationInitial with the extracted command and its arguments
        
        operands = [operand.name for operand in parsed_command_invocation.operand_list]
        
        # Default output type is just file paths
        output_type = RegularType(".+")
        
        # Flag to track if we found an -exec command
        found_exec = False
        
        # Check for -exec flag
        for i in range(len(operands) - 3):  # Need at least 4 tokens for -exec cmd {} \;/+
            # Check if we have "-e", "-x", "-e", "-c" in sequence which represents "-exec"
            if (i + 3 < len(operands) and 
                operands[i] == "-e" and 
                operands[i+1] == "-x" and 
                operands[i+2] == "-e" and 
                operands[i+3] == "-c"):
                
                found_exec = True
                
                # Extract the command and its arguments
                cmd_index = i + 4
                if cmd_index < len(operands):
                    cmd_name = operands[cmd_index]
                    cmd_args = []
                    
                    # Collect all arguments until we reach the terminator (';' or '+')
                    j = cmd_index + 1
                    while j < len(operands) and operands[j] != ";" and operands[j] != "+":
                        # Skip '{}' placeholder as it's a special marker
                        if operands[j] != "{}":
                            cmd_args.append(operands[j])
                        j += 1
                    
                    # Create a new CommandInvocationInitial for the extracted command
                    from pash_annotations.datatypes.BasicDatatypes import Operand, Flag, Option
                    
                    # Convert arguments to appropriate types (Flag, Option, or Operand)
                    flag_option_list = []
                    operand_list = []
                    
                    for arg in cmd_args:
                        if arg.startswith('-'):
                            if '=' in arg:
                                option_name, option_arg = arg.split('=', 1)
                                flag_option_list.append(Option(option_name, option_arg))
                            else:
                                flag_option_list.append(Flag(arg))
                        else:
                            operand_list.append(Operand(arg))
                    
                    # Create the command invocation
                    exec_command = CommandInvocationInitial(cmd_name, flag_option_list, operand_list)
                    
                    # Find a matching command signature and infer its output type
                    from stream.signature_loader import SignatureLoader
                    loader = SignatureLoader.get_instance()
                    
                    for signature in loader.signatures:
                        if signature.matches_command(exec_command):
                            exec_output = signature.output_type_inference(RegularType(".+"), exec_command, env_annotations)
                            if isinstance(exec_output, InferenceResult):
                                output_type = exec_output.output_type
                            else:
                                output_type = exec_output

                            # Special case for 'ls' command: remove "total" line from output type
                            if cmd_name == "ls":
                                output_type = output_type - RegularType("total .+")

                            break
                    
                    # Found an -exec, no need to search further
                    break
        
        # If no -exec was found, infer type based on the specified path
        if not found_exec and operands:
            # The first operand is typically the search path
            search_path = operands[0]
            
            # If the path looks like an actual path (not a flag or option)
            if not search_path.startswith('-'):
                # Check for name/type patterns in the operands
                name_pattern = None
                for i in range(len(operands) - 1):
                    if operands[i] == "-name" and i + 1 < len(operands):
                        name_pattern = operands[i + 1]
                        break
                
                # Convert glob pattern to regex if found
                if name_pattern and ('*' in name_pattern or '?' in name_pattern):
                    # Convert glob pattern to regex pattern
                    # Escape special characters except * and ?
                    regex_pattern = re.escape(name_pattern).replace('\\*', '.*').replace('\\?', '.')
                    
                    # Escape the path for regex
                    escaped_path = re.escape(search_path)
                    
                    # Build the full pattern
                    if search_path.endswith('/'):
                        # If path ends with slash, handle differently
                        output_type = RegularType(f"{escaped_path}.*{regex_pattern}")
                    else:
                        # Pattern matches the path and its subdirectories with the name pattern
                        output_type = RegularType(f"{escaped_path}(/.*)?/{regex_pattern}")
                else:
                    # No name pattern found, use the default path-based inference
                    # Escape the path for regex and build the pattern
                    escaped_path = re.escape(search_path)
                    if search_path.endswith('/'):
                        # If path ends with slash, handle differently
                        output_type = RegularType(f"{escaped_path}.*")
                    else:
                        # Pattern matches the path itself or any subdirectory/file under it
                        output_type = RegularType(f"{escaped_path}(/.+)?")
        return InferenceResult(output_type, None, False)
