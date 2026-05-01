# RT

## Artifact evaluation
To evaluate the artifact for the OSDI'26 paper titled "RT: Regular Types for the Streaming Shell", jump straight to [INSTRUCTIONS.md](INSTRUCTIONS.md).

RT is a prototype for statically checking shell pipelines with stream-type reasoning, command models, and optional user annotations. This repository includes the checker implementation, the benchmark suites used in the evaluation, and the scripts used to regenerate the reported outputs.

The root `README.md` is the short artifact-facing entry point. The fuller artifact-evaluation flow, including badge-oriented instructions and the longer reproduction path, is in `INSTRUCTIONS.md`.

## Getting Started Instructions

The recommended path is Docker.

From the repository root:

```bash
docker build -t rt-artifact .
docker run --rm -it -v "$(pwd):/home/StreamTypes" rt-artifact
```

Inside the container, run:

```bash
bash scripts/check_functionality.sh
```

This script runs the unit test suite and one smoke test on `examples/motivating_example.sh` through the top-level `rt.sh` entry point. These commands are enough for the artifact-functional path. For the full reproduction path, including the baseline comparison, see the detailed instructions below and `INSTRUCTIONS.md`.

## Manual Host Installation (Optional)

If you prefer to install the artifact directly on your own machine instead of using Docker, set up:

- Python packages:

```bash
python3 -m pip install -r requirements.txt
```

- Java runtime, because the checker loads `jars/automaton.jar` through JPype

## Detailed Instructions

The main entry points are:

- `bash scripts/check_functionality.sh` for the artifact-functional path: unit tests plus one RT smoke test,
- `bash scripts/reproduce_full.sh` for the full paper pipeline.

The benchmark directories used by the batch runner are configured in `src/stream/config/config.yaml`. By default they include the small handwritten and ladder examples in `full_benchmark/handwritten/` and `full_benchmark/ladder/`, plus the larger corpora in `full_benchmark/`.

### Manual Host Installation For Full Paper Pipeline (Optional)

If you are not using Docker for the full paper pipeline, additionally install the baseline-comparison dependencies:

- `shellcheck`

```bash
sudo apt-get install shellcheck
```

- Rust toolchain for building `ltsh`

```bash
sudo apt-get install cargo rustc
```

- upstream `ltsh`, available on `PATH`

```bash
LTSH_CHECKOUT=/path/to/ltsh
git clone --depth 1 --branch dev https://github.com/michaelsippel/ltsh "$LTSH_CHECKOUT"
cargo install --path "$LTSH_CHECKOUT"
```

Keep the cloned `ltsh` checkout in place after `cargo install --path ...`: upstream `ltsh` resolves `gettype.sh` relative to the cloned source tree at runtime.

In `src/stream/config/config.yaml`, `shellcheck_command`, `ltsh_command`, and `ltsh_typedb_path` control the external tool paths.

If you prefer macOS or another platform, install `shellcheck` and Rust through your platform package manager, make sure a Java runtime is available, then use the same `git clone` and `cargo install` steps.

To reproduce the main RT results and regenerate the paper artifacts, run:

```bash
bash scripts/reproduce_full.sh
```

To force regeneration even when cached outputs already exist:

```bash
bash scripts/reproduce_full.sh --force
```

The RT runs and ablations, the derived summary CSVs under `evaluation_results/derived/`, and the PDFs under `evaluation_results/plots/`.

The bug-detection plot compares the unannotated RT run against ShellCheck and LadderTypes, with the RT system labeled simply as `RT`.

Cleanup for optional local installation: if you installed `ltsh`, `shellcheck`, or Python packages only for this artifact review, remove those installed packages if they are not needed, and remove the cloned `ltsh` checkout.

The expanded guide, including artifact-available, artifact-functional, and results-reproducible instructions, is in `INSTRUCTIONS.md`.
