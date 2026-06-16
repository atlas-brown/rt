import argparse

from stream.parser.shell_parser_util import annot_parser_wrapper as parse_invocation
from stream.regular_type import RegularType
from stream.signature_loader import SignatureLoader


def cli_main():
    parser = argparse.ArgumentParser(description="Regular type resolution")
    parser.add_argument(
        "command",
        type=str,
        help="The command to resolve the regular type for",
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        type=str,
        help="The invocation args to resolve the regular type for",
    )
    parser.add_argument(
        "-i",
        "--input-type",
        type=str,
        default=None,
        help="The regular type of the supposed input to the invocation",
    )
    args = parser.parse_args()
    input_type = None
    if args.input_type is not None:
        input_type = RegularType(args.input_type)
    main(args.command, args.args, input_type)


def main(command: str, args: list[str], prev_out_type: RegularType | None):
    invocation = parse_invocation([command, *args])
    loader = SignatureLoader.get_instance()
    signature = loader.load_signature(invocation.cmd_name)

    # Determine input type
    if prev_out_type is None:
        in_type, _ = signature.determine_input_type(invocation, [], [], {})
        in_pattern = in_type.pattern
    else:
        in_pattern = prev_out_type.pattern
    assert isinstance(in_pattern, str), "nooooo"

    # Determine output type
    if prev_out_type is None:
        prev_out_type = RegularType(".*")

    command_type = signature.determine_command_type(invocation, [], {})
    out_type = signature.apply_command_type(command_type, prev_out_type).output_type
    out_pattern = out_type.pattern
    assert isinstance(out_pattern, str), "nooooo"

    print("Invocation:")
    print(" ".join((command, *args)))
    print()
    print("Type:")
    print(in_pattern + " -> " + out_pattern)


if __name__ == "__main__":
    cli_main()
