from stream.shell_parser_util import parse_shell_to_asts
from sys import argv

if __name__ == "__main__":
    shell_script = argv[1]
    parse_shell_to_asts(shell_script)