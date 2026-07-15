import argparse
import logging
import os
import sys
from pathlib import Path

from rt.format import format_compact, format_human, format_json
from rt.shell.parser import Pipeline, parse_pipelines
from rt.type_checking.checker import TypeCheckError, type_check

_LOG_ENV_VAR = "RT_LOG_LEVEL"
_LOG_LEVELS = logging.getLevelNamesMapping()


def cli_main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        help="The shell script to analyze; leave empty for interactive use",
    )
    parser.add_argument(
        "-L",
        "--log-level",
        metavar="LEVEL",
        type=str.upper,
        choices=_LOG_LEVELS.keys(),
        help=argparse.SUPPRESS,  # Hidden argument
    )

    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument(
        "--compact",
        action="store_true",
        help="Use compact single-line error output",
    )
    format_group.add_argument(
        "--json",
        action="store_true",
        help="Output errors in JSON format",
    )

    args = parser.parse_args()
    exit_code = main(
        file=args.file,
        use_json=args.json,
        use_compact=args.compact,
        log_level=args.log_level,
    )
    sys.exit(exit_code)


def main(
    file: Path | None = None,
    use_json: bool = False,
    use_compact: bool = False,
    log_level: str | None = None,
) -> int:
    configure_logging(log_level)

    if file is not None:
        it = iter((file,))
    else:
        it = (line.strip() for line in sys.stdin if line.strip())
        if sys.stdin.isatty():
            print("Reading pipelines from stdin; use Ctrl+D to exit")

    had_type_errors = False
    had_system_error = False

    for elem in it:
        for pipeline in parse_pipelines(elem):
            logging.debug("Parsed pipeline: %r", pipeline)
            errors, system_error = _safe_type_check(pipeline)
            if system_error:
                had_system_error = True
            for err in errors:
                had_type_errors = True
                logging.debug("Got error: %r", err)
                print(
                    format_error(
                        err, pipeline, use_json=use_json, use_compact=use_compact
                    )
                )

    if had_system_error:
        return 2
    if had_type_errors:
        return 1
    return 0


def _safe_type_check(
    pipeline: Pipeline,
) -> tuple[list[TypeCheckError], bool]:
    try:
        return list(type_check(pipeline)), False
    except Exception:
        return [], True


def configure_logging(log_level: str | None) -> None:
    if (log_level := log_level or os.environ.get(_LOG_ENV_VAR)) is not None:
        log_level = log_level.upper()
        if log_level not in _LOG_LEVELS:
            print(
                f"rt: unknown log level '{log_level}', using 'WARNING'", file=sys.stderr
            )
            log_level = "WARNING"

        logging.basicConfig(
            level=_LOG_LEVELS[log_level],
            format="%(levelname)s [%(name)s] %(message)s",
        )


def format_error(
    error: TypeCheckError, pipeline: Pipeline, *, use_json: bool, use_compact: bool
):
    if use_json:
        return format_json([error], pipeline)
    if use_compact:
        return format_compact([error], pipeline)
    return format_human([error], pipeline)


if __name__ == "__main__":
    cli_main()
