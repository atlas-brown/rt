from __future__ import annotations

import argparse
import pathlib
from collections.abc import Sequence

from rtr.main import LOG_LEVELS, check_file, interactive_check


def cli_main() -> None:
    raise SystemExit(main_cli())


def main_cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run RT on a shell script.")
    parser.add_argument(
        "file",
        nargs="?",
        type=pathlib.Path,
        help="The shell script to analyze; leave empty for interactive use.",
    )
    parser.add_argument(
        "-d",
        "--disable-annotations",
        action="store_true",
        help="Ignore user-provided annotations.",
    )
    parser.add_argument(
        "-L",
        "--log-level",
        metavar="LEVEL",
        choices=LOG_LEVELS,
        default="DISABLED",
        help="Set the logging level (default: %(default)s).",
    )
    args = parser.parse_args(argv)
    if args.file is None:
        return interactive_check(args.disable_annotations, args.log_level)
    return check_file(args.file, args.disable_annotations, args.log_level)


if __name__ == "__main__":
    cli_main()
