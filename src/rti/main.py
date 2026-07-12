import argparse
import hashlib
import json
import re
from pathlib import Path

import yaml

from stream.command_type_parser import parse_command_type_annotation
from stream.parser.shell_parser_util import annot_parser_wrapper as parse_invocation
from stream.regular_type import RegularType
from stream.signature_loader import SignatureLoader
from stream.type_alias import save_custom_alias, get_type_name, resolve_type_from_name


DEFAULT_SIGNATURE_DIR = "./src/stream/signatures"


def cli_main():
    parser = argparse.ArgumentParser(description="Regular type resolution")
    parser.add_argument(
        "--signature-dir",
        type=Path,
        default=Path(DEFAULT_SIGNATURE_DIR),
        help="Directory containing command signature YAML files.",
    )
    parser.add_argument(
        "-t",
        "--type",
        "--type-annotation",
        dest="type_annotation",
        default=None,
        help="Persist a command type annotation for this exact invocation, e.g. '[0-9]+ -> [0-9]+' or 'forall a . a -> a'.",
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
        help="Add a new user defined type alias."
    )
    parser.add_argument(
        "--show-type",
        help="Shows the resolved type."
    )
    args = parser.parse_args()

    try:
        if args.def_type is not None:
            raw_in = args.def_type
            if "::" not in raw_in:
                parser.error("Invalid format for --def-type. Use: name :: expression")
            
            name, exp = raw_in.split("::", 1)

            name = name.strip()
            exp = exp.strip()

            if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
                parser.error(f"Invalid alias name: '{name}'. Only alphanumeric, underscores, and dashes allowed.")
            
            save_custom_alias(name, exp)
            print(f"Success: Registered alias [[:{name}:]] -> {exp}")
            return
        
        if args.show_type is not None:
            raw_in = args.show_type
            if "->" not in raw_in:
                parser.error("Invalid format for --show-type. Use: type -> type")
            
            name1, name2 = raw_in.split("->", 1)
            name1 = name1.strip()
            name2 = name2.strip()

            type_name1 = get_type_name(name1)
            if type_name1 is not None:
                exp1 = resolve_type_from_name(type_name1)
                if exp1 is not None:
                    name1 = exp1

            type_name2 = get_type_name(name2)
            if type_name2 is not None:
                exp2 = resolve_type_from_name(type_name2)
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
            input_type = RegularType(args.input_type)
        main(
            args.command,
            args.args,
            input_type,
            signature_dir=args.signature_dir,
            type_annotation=args.type_annotation,
        )

    except ValueError as e:
        parser.error(str(e))


def _safe_file_part(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return value or "command"


def _flag_option_value(flag_option) -> str | None:
    for attr in ("arg", "argument", "option_arg", "value"):
        if hasattr(flag_option, attr):
            value = getattr(flag_option, attr)
            return str(value) if value is not None else None
    for method_name in ("get_arg", "get_argument", "get_option_arg", "get_value"):
        method = getattr(flag_option, method_name, None)
        if callable(method):
            value = method()
            return str(value) if value is not None else None
    return None


def _invocation_match(invocation) -> dict:
    flag_options = []
    for flag_option in invocation.flag_option_list:
        entry = {"name": flag_option.get_name()}
        value = _flag_option_value(flag_option)
        if value is not None:
            entry["value"] = value
        flag_options.append(entry)

    return {
        "flag_options": flag_options,
        "operands": [operand.name for operand in invocation.operand_list],
    }


def _annotation_file_path(signature_dir: Path, match: dict, command_name: str) -> Path:
    payload = {"command_name": command_name, "match": match}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    return signature_dir / f"{_safe_file_part(command_name)}__annotation_{digest}.yaml"


def register_invocation_type(
    invocation,
    signature_dir: Path,
    type_annotation: str,
) -> Path:
    signature_dir.mkdir(parents=True, exist_ok=True)
    match = _invocation_match(invocation)
    parsed_annotation = parse_command_type_annotation(type_annotation)
    signature_data = parsed_annotation.to_signature_data(invocation.cmd_name, match)

    annotation_path = _annotation_file_path(signature_dir, match, invocation.cmd_name)
    annotation_path.write_text(
        yaml.safe_dump(signature_data, sort_keys=False),
        encoding="utf-8",
    )
    return annotation_path


def find_signature(loader: SignatureLoader, invocation):
    return loader.find_signature(invocation)


def _display_pattern(regular_type: RegularType) -> str:
    if regular_type.get_singleton() is not None:
        return regular_type.get_singleton()
    if regular_type.get_type_alias() is not None:
        return regular_type.get_type_alias()
    if regular_type.pattern is not None:
        return regular_type.pattern
    return repr(regular_type)


def main(
    command: str,
    args: list[str],
    prev_out_type: RegularType | None,
    signature_dir: Path | str = DEFAULT_SIGNATURE_DIR,
    type_annotation: str | None = None,
):
    signature_dir = Path(signature_dir)
    invocation = parse_invocation([command, *args])
    SignatureLoader.reset_instance()
    loader = SignatureLoader.get_instance(signature_dir.as_posix())

    if type_annotation is not None:
        annotation_path = register_invocation_type(
            invocation,
            signature_dir,
            type_annotation,
        )
        loader.reload()
        print(f"Registered type annotation: {annotation_path}")

    signature = find_signature(loader, invocation)

    # Determine input type
    if prev_out_type is None:
        in_type, _, _ = signature.determine_input_type(invocation, [], [], {})
        in_pattern = _display_pattern(in_type)
        inferred_input_type = in_type
    else:
        in_pattern = _display_pattern(prev_out_type)
        inferred_input_type = prev_out_type

    command_type = signature.determine_command_type(invocation, [], {})

    if prev_out_type is None: 
        print("Invocation:")
        print(" ".join((command, *args)))
        print()
        print("Type:")
        print(command_type)
        return

    # Determine output type
    if prev_out_type is None:
        prev_out_type = inferred_input_type
    
    out_type = signature.apply_command_type(command_type, prev_out_type)
    out_pattern = _display_pattern(out_type)

    print("Invocation:")
    print(" ".join((command, *args)))
    print()
    print("Polymorphic Type:")
    print(command_type)
    print()
    print("Instatiated Type:")
    print(in_pattern + " -> " + out_pattern)


if __name__ == "__main__":
    cli_main()
