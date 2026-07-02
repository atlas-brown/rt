# RT Artifact README

To evaluate the artifact for the OSDI'26 paper titled "RT: Regular Types for the Streaming Shell", jump straight to [INSTRUCTIONS.md](INSTRUCTIONS.md).

## Getting Started Instructions

RT is a prototype for statically checking shell pipelines with regular types, command models, finite-state reasoning, and optional user annotations. This artifact includes the checker implementation, the benchmark suites used in the paper evaluation for functional checks and result reproduction.

The fastest way to check the basic functionality is to use the provided Docker image. From the repository root, build the image and start a shell in it:

```sh
docker build --target dev -t rt-artifact .
docker run --rm -it -v "$(pwd):/home/StreamTypes" rt-artifact
```

Inside the container, run:

```sh
bash scripts/check_functionality.sh
```

Equivalently, run the same check directly from the host with the same image:

```sh
docker run --rm -v "$(pwd):/home/StreamTypes" rt-artifact bash scripts/check_functionality.sh
```

This script runs the unit test suite and then runs RT on `examples/motivating_example.sh` through the top-level `rt.sh` entry point. The smoke test should print the first expected RT diagnostic for the motivating example. This is the short artifact-functional path and should complete within the short review window.

For local host installation instead of Docker, install the Python requirements and a Java runtime before running the same command.

## Command-Line Interfaces

RT exposes two command-line interfaces through the project environment:

1. `rt` checks shell scripts and pipelines.
2. `rti` queries and updates the regular type.

### `rt`: check scripts and pipelines

Use `rt` when you want to analyze a shell script or an ad hoc pipeline. The
interface can check a shell script from a file, or it can read one pipeline at a
time interactively from standard input.

Inside the Docker shell from the quickstart, invoke the checker with `uv run`:

```sh
uv run rt examples/motivating_example.sh
```

When RT finds a pipeline type error, it prints the diagnostic and exits
with status `1`. If no RT errors are found, it prints `No RT errors found.` and
exits with status `0`.

### `rti`: resolve command types

Use `rti` when you want to inspect the regular type of a single command invocation. It prints the invocation and the resolved input-to-output type.

```sh
uv run rti echo hello
```

Example output:

```text
Invocation:
echo hello

Type:
∀α[α ⊆ RegularType(.*)]. α -> Constant(RegularType(hello))
```

```sh
uv run rti -i echo hello
```

Example output:

```text
Invocation:
hello

Type:
echo -> .*
```

You can also use `rti` to update a type annotation for one exact command
invocation:

```sh
uv run rti --type '[0-9]+ -> [0-9]+' my_command --my-flag
```

## Detailed Instructions

The main entry points are:

1. `bash scripts/check_functionality.sh` for the short functionality check.
2. `bash scripts/reproduce_full.sh --force` for the full paper-result reproduction.

When using the Docker image, run the full reproduction with the same image:

```sh
docker run --rm -v "$(pwd):/home/StreamTypes" rt-artifact bash scripts/reproduce_full.sh --force
```

The full reproduction pipeline runs the baseline comparison, the main RT configuration, the ablations, and the plot/table generation with the project Python environment. Its runtime depends on the machine and storage speed; on a typical review machine, expect roughly one hour.

The primary outputs to inspect after full reproduction are:

1. `evaluation_results/tables/ablation_table.md`
2. `evaluation_results/tables/timing_table.md`
3. `evaluation_results/plots/accuracy-chart-with-annotations.pdf`
4. `evaluation_results/plots/accuracy-chart-without-annotations.pdf`
5. `evaluation_results/plots/bug-detection.pdf`
6. `evaluation_results/plots/automata-sizes.pdf`

The benchmark directories and output paths are configured in `src/stream/config/config.yaml`. For local non-Docker reproduction, make sure Python, Java, ShellCheck, Rust, and LadderTypes are available before running the full pipeline.
