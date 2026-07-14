import argparse
import re
from pathlib import Path

import rt.regular_types.database.registry as registry
from rt.regular_types.command_type import CommandType
from rt.regular_types.database.resolver import RuleResolver
from rt.regular_types.stream_type import StreamType
from rt.shell.parser import parse_invocation


def _parse_type_annotation(annotation: str) -> tuple[str, str]:
    match = re.fullmatch(r"\s*(.+?)\s*->\s*(.+?)\s*", annotation)
    if match is None:
        raise ValueError(
            f"Invalid type annotation: {annotation!r}. Expected 'input -> output'."
        )
    return match.group(1), match.group(2)


def cli_main():
    parser = argparse.ArgumentParser(description="Regular type resolution")
    parser.add_argument(
        "-t",
        "--type",
        "--type-annotation",
        dest="type_annotation",
        default=None,
        help=(
            "Persist a command type annotation for this invocation, "
            "e.g. '[0-9]+ -> [0-9]+'."
        ),
    )
    parser.add_argument(
        "command",
        type=str,
        nargs="?",
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
        help="The regular type of the supposed input to the invocation when resolving it.",
    )
    parser.add_argument(
        "--def-type",
        help="Add a new user defined type alias.",
    )
    parser.add_argument(
        "--show-type",
        help="Shows the resolved type.",
    )
    args = parser.parse_args()

    try:
        if args.def_type is not None:
            raw_in = args.def_type
            if "::" not in raw_in:
                parser.error(
                    "Invalid format for --def-type. Use: name :: expression"
                )

            name, exp = raw_in.split("::", 1)

            name = name.strip()
            exp = exp.strip()

            if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
                parser.error(
                    f"Invalid alias name: '{name}'. "
                    "Only alphanumeric, underscores, and dashes allowed."
                )

            registry.save_alias(name, exp)
            print(f"Success: Registered alias [[:{name}:]] -> {exp}")
            return

        if args.show_type is not None:
            raw_in = args.show_type
            if "->" not in raw_in:
                parser.error("Invalid format for --show-type. Use: type -> type")

            name1, name2 = raw_in.split("->", 1)
            name1 = name1.strip()
            name2 = name2.strip()

            type_name1 = registry.get_type_name(name1)
            if type_name1 is not None:
                exp1 = registry.resolve_type_from_name(type_name1)
                if exp1 is not None:
                    name1 = exp1

            type_name2 = registry.get_type_name(name2)
            if type_name2 is not None:
                exp2 = registry.resolve_type_from_name(type_name2)
                if exp2 is not None:
                    name2 = exp2

            print()
            print("Resolved Types:")
            print(name1, "->", name2)
            return

        if args.command is None:
            parser.error("the following are required: command")

        input_type = None
        if args.input_type is not None:
            input_type = StreamType.from_pattern(args.input_type)
        main(
            args.command,
            args.args,
            input_type,
            type_annotation=args.type_annotation,
        )

    except ValueError as e:
        parser.error(str(e))


def _display_pattern(st: StreamType) -> str:
    return st.regex or repr(st)


def main(
    command: str,
    args: list[str],
    prev_out_type: StreamType | None,
    type_annotation: str | None = None,
):
    invocation = parse_invocation([command, *args])

    if type_annotation is not None:
        in_regex, out_regex = _parse_type_annotation(type_annotation)
        resolver = RuleResolver(input_type=in_regex, output_type=out_regex)
        registry.register_type(invocation.cmd_name, resolver)
        print(f"Registered type annotation for {invocation.cmd_name}")

    cmd_type: CommandType = registry.get_type(invocation)

    if prev_out_type is None:
        print("Invocation:")
        print(" ".join((command, *args)))
        print()
        print("Type:")
        print(cmd_type)
        return

    out_type = cmd_type.apply(prev_out_type, {})
    in_pattern = _display_pattern(prev_out_type)
    out_pattern = _display_pattern(out_type)

    print("Invocation:")
    print(" ".join((command, *args)))
    print()
    print("Polymorphic Type:")
    print(cmd_type)
    print()
    print("Instatiated Type:")
    print(in_pattern + " -> " + out_pattern)


if __name__ == "__main__":
    cli_main()
