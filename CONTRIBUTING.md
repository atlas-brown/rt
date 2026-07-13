# Contributing to Rt

## Getting started

Rt uses [uv](https://docs.astral.sh/uv/) for dependency management and
[pytest](https://docs.pytest.org/) for testing. A Java runtime is required --
the checker loads automaton operations through JPype.

```sh
git clone https://github.com/atlas-brown/rt.git
cd rt
uv sync
```

### Running tests

```sh
uv run pytest
```

To run tests for a specific component:

```sh
uv run pytest tests/rt/
```

### VS Code devcontainer

Open the repo in VS Code with the Dev Containers extension installed. The
devcontainer provisions all dependencies automatically, including Java.

## Project structure

```
src/
├── rt/                    # CLI for checking shell scripts ("rt")
│   ├── main.py            # Entry point
│   ├── shell/             # Shell script parser & AST
│   ├── type_checking/     # Pipeline type checker, annotations, heuristics
│   ├── regular_types/     # Regular type & automaton abstractions
│   ├── transducer.py      # Finite-state transducers
│   ├── regex/             # Regex parser & AST
│   ├── format.py          # Error output formatting
│   ├── java_api.py        # JPype bridge to automaton engine
│   ├── constants.py       # Configuration constants
│   ├── automaton_to_regex.py  # Automaton-to-regex serialization
│   └── utils.py           # General utilities
└── rti/                   # CLI for inspecting command types ("rti")
    └── main.py            # Entry point
```

## Need help?

Open an issue at <https://github.com/atlas-brown/rt/issues>.
