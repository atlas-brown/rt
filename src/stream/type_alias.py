import re
import json
from pathlib import Path

BUILTIN_TYPE_ALIASES = {
    "filename":      r"[^/\n]+",
    "mask":          r"[rwx-]{9}",
    "base64":        r"(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?",
    "integer":       r"-?[0-9]+",
    "float":         r"-?(?:[0-9]+\.[0-9]*|\.[0-9]+)",
    "md5":           r"[A-Fa-f0-9]{32}",
    "sha128":        r"[A-Fa-f0-9]{32}",
    "sha256":        r"[A-Fa-f0-9]{64}",
    "number":        r"-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)",
    "day-of-the-week": r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon|Tue|Wed|Thu|Fri|Sat|Sun)",
    "month":         r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
    "hh:mm:ss":      r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]",
    "year":          r"[0-9]{4}",
    "username":      r"[a-z_][a-z0-9_-]*",
    "hh:mm":         r"(?:[01][0-9]|2[0-3]):[0-5][0-9]",
    "absolute-path": r"/.*",
    "ip-address":    r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}",
}

# This creates ~/.config/rti/custom_types.json
CUSTOM_TYPES_FILE = Path.home() / ".config" / "rti" / "custom_types.json"

def load_custom_types_to_dict() -> dict[str, str]:
    if not CUSTOM_TYPES_FILE.exists():
        return {}
    try:
        with open(CUSTOM_TYPES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}
    
def save_custom_alias(name: str, exp: str):
    custom_aliases = load_custom_types_to_dict()

    custom_aliases[name] = exp

    CUSTOM_TYPES_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(CUSTOM_TYPES_FILE, "w") as f:
        json.dump(custom_aliases, f, indent=4)


def get_type_name(type_exp: str) -> str | None:
    match = re.fullmatch(r"\[\[:([A-Za-z0-9_-]+):\]\]", type_exp)
    if match:
        return match.group(1)
    return None

def resolve_type_from_name(type_name: str) -> str | None:

    if type_name in BUILTIN_TYPE_ALIASES:
        return BUILTIN_TYPE_ALIASES[type_name]
    
    custom_aliases = load_custom_types_to_dict()
    if type_name in custom_aliases:
        return custom_aliases[type_name]
    return None

def resolve_name_from_exp(exp: str) -> str | None:
    for k,v in BUILTIN_TYPE_ALIASES.items():
        if v == exp:
            return f"[[:{k}:]]"
    
    custom_aliases = load_custom_types_to_dict()
    for k,v in custom_aliases.items():
        if v == exp:
            return f"[[:{k}:]]"
    
    return None

