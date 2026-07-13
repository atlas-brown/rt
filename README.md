# Rt: An overlay type system for shell pipelines

Jump to: [How it works](#how-it-works) | [Features](#features) | [User annotations](#user-annotations) | [Installation](#installation) | [Usage](#usage) | [Documentation](#documentation) | [Citing](#citing) | [Contributing](#contributing)

Rt catches data incompatibilities in shell pipelines before they run. Give it a
shell program and it tells you when one command produces data the next command
can't consume -- with a concrete counterexample showing exactly what breaks.

```
$ cat pipeline.sh
find . |
grep -E 'book[0-9]+\.txt' |
xargs cat
```

```
$ rt pipeline.sh
Error (ln. 1): grep → xargs
    grep produced '[^n]*' but xargs expects '([^[:blank:]]+|".+"|'.+')'
    Counterexample: " "
```

`grep -E 'book[0-9]+\.txt'` produces filenames -- including ones with spaces
or tabs. But `xargs` splits its input on whitespace, so a file named
`my book1.txt` would be split into two arguments: `my` and `book1.txt`.
Rt catches this mismatch and tells you exactly what triggers it.

## How it works

Rt gives each position in a pipeline a *regular type* -- a regular expression
describing the shape of every line that can appear at that point. For example,
after `grep -E '^[0-9]+$'`, the output type is lines consisting only of digits;
after `cut -d, -f1`, the output type is lines containing no commas.

Commands are modeled as transformations from input type to output type. Simple
commands like `echo` produce a fixed output regardless of input. Filtering
commands like `grep` produce output that is a subset of their input. Commands
that reshape data character-by-character -- `tr`, `cut`, `head` -- are modeled
with *finite-state transducers* that precisely describe how each input line is
rewritten into an output line.

To check a pipeline, Rt walks the commands left-to-right, composing these
transformations. At each step it verifies that the previous command's output
type is compatible with the next command's input type. If not, it reports a
counterexample: a concrete string that triggers the mismatch.

## Features

- **Pipeline type checking.** Verify that the output of each command in a
  pipeline is compatible with the input of the next.
- **Concrete counterexamples.** Every error includes a witness string that
  triggers the incompatibility, not just a vague warning.
- **Polymorphic command models.** Commands like `grep` and `cut` are modeled as
  input-dependent transformations, so the checker adapts to your pipeline's
  actual data.
- **User annotations.** Embed type expectations directly in shell comments to
  guide the checker or verify properties:

  ```sh
  # @assume "gen_books.sh" --> "^[A-Z][a-z]+ [0-9]+$"
  gen_books.sh |
  # @expect "[0-9]+" --> "grep -E '^[0-9]-[0-9]+-[0-9]+-[0-9A-Z]$'"
  grep -E '^[0-9]-[0-9]+-[0-9]+-[0-9A-Z]$'
  ```

- **Finite-state transducers.** Character-level transformations for commands
  like `tr`, `cut`, and `head`.
- **Interactive type inspection.** Use `rti` to query the type of any command
  invocation.

## User annotations

Annotations are shell comments placed on the line immediately above a pipeline
or command. They start with `# @` followed by a keyword and quoted arguments.
The `command` field in command-level annotations must be the full invocation
including all flags and arguments (e.g. `"grep -E 'pattern'"`, not just
`"grep"`).

### Command-level annotations

| Annotation | Syntax | Description |
|---|---|---|
| `@assume` | `# @assume "invocation" --> "regex"` | Declare that the command's output matches the regex |
| `@expect` | `# @expect "regex" --> "invocation"` | Declare the expected input type for a command (stored, not yet verified) |
| `@assert` | `# @assert "invocation" --> "regex"` | Assert that a command's output conforms to the regex |
| `@assert_contains` | `# @assert_contains "invocation" --> "regex"` | Assert that a command's input contains strings matching the regex |

### Pipeline-level annotations

| Annotation | Syntax | Description |
|---|---|---|
| `@input` | `# @input "regex"` | Declare the expected input type for the entire pipeline |
| `@output` | `# @output "regex"` | Assert the pipeline's output conforms to the regex |
| `@output_contains` | `# @output_contains "regex"` | Assert the pipeline's output contains strings matching the regex |

### Environment annotations

| Annotation | Syntax | Description |
|---|---|---|
| `@file` | `# @file "$varname" : "regex"` | Declare the type of a file operand's content |
| `@var` | `# @var "$varname" : "regex"` | Declare the type of a non-file shell variable |
| `@concretize` | `# @concretize "varname" --> "path"` | Concretize a file variable by reading its content from `path` |

## Installation

The quickest way to get started:

```sh
curl -fsSL https://raw.githubusercontent.com/atlas-brown/rt/main/scripts/install.sh | sh
```

This downloads a thin `rt` wrapper to `~/.local/bin` that runs Rt in Docker.
Make sure `~/.local/bin` is on your `PATH`. Requires [Docker](https://docs.docker.com/get-docker/).

### Build from source

If you'd rather run natively, Rt uses [uv](https://docs.astral.sh/uv/) for
dependency management. You will need a Java runtime -- the checker loads
automaton operations through JPype.

```sh
git clone https://github.com/atlas-brown/rt.git
cd rt
uv sync
uv run rt --help
```

Make sure `java` is on your `PATH` and `JAVA_HOME` is set before running.

## Usage

### `rt` -- check programs and pipelines

```sh
# Check a shell program file
rt program.sh

# Check a pipeline interactively (reads from stdin)
rt
```

Rt prints diagnostics for each type error it finds. If no errors are found,
nothing is printed and the exit status is `0`.

Output formats: `--compact` (single-line output) or `--json` (structured JSON).

### `rti` -- inspect command types

```sh
# Show the polymorphic type of a command
rti echo hello

# Show the input-to-output type of a command
rti -i hello grep o

# Register a custom type annotation for a command
rti --type '[0-9]+ -> [0-9]+' my_command --my-flag
```

`rti --type` persists the annotation as a YAML file under the signatures
directory, so subsequent `rt` runs will use it.

## Documentation

- [Architecture overview](docs/architecture.md) -- how the checker works under
  the hood: stream types, command types, transformations, stream transformers,
  and the automaton engine.
- [Command signatures](docs/command-signatures.md) -- how to define and
  register custom command types, including YAML format, output expressions,
  extended modules, and `rti --type` registration.

## Citing

If you use Rt in your research, please cite:

```bibtex
@inproceedings{rt:osdi:2026,
  title     = {Rt: Regular Types for the Streaming Shell},
  author    = {Li, Zekai and Lazarek, Lukas and Lamprou, Evangelos and Kapetanakis, George and Mamouras, Konstantinos and Vasilakis, Nikos},
  year      = {2026},
  booktitle = {20th USENIX Symposium on Operating Systems Design and Implementation (OSDI 26)},
  publisher = {USENIX Association},
  url       = {https://www.usenix.org/conference/osdi26/presentation/li-zekai},
  artifact  = {https://github.com/atlas-brown/rt},
  tags      = {correctness}
}
```

## Contributing

Rt is a research prototype from the [ATLAS Group](https://atlas.cs.brown.edu/). We welcome contributions. See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, project layout, and guidelines.
