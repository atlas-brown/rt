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

These commands are enough for the artifact-functional path. For the full reproduction path, including the baseline comparison, see the detailed instructions below and `INSTRUCTIONS.md`.

## Manual Host Installation (Optional)

If you prefer to install the artifact directly on your own machine instead of using Docker, set up:

- Python packages:

```bash
python3 -m pip install -r requirements.txt
```

- Java runtime, because the checker loads `jars/automaton.jar` through JPype

## Detailed Instructions

The main entry points are:

- `bash scripts/check_functionality.sh` for the artifact-functional path,
- `bash scripts/reproduce_full.sh` for the full paper pipeline,
- `sh typecheck.sh -f <pipeline-file>` for ad hoc single-pipeline checking,
- `./run_evaluations.sh` for ad hoc batch evaluation over the configured corpora.

The benchmark directories used by the batch runner are configured in `src/stream/config/config.yaml`. By default they include the small handwritten examples in `evaluation_pipelines/` plus the larger corpora in `full_benchmark/`.

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

- upstream `ltsh`, with this repository's typedb replacing the upstream one

```bash
git clone --depth 1 --branch dev https://github.com/michaelsippel/ltsh "$HOME/.local/src/ltsh"
cp ltsh_config/typedb "$HOME/.local/src/ltsh/typedb"
cargo install --path "$HOME/.local/src/ltsh"
export TYPEDB="$(pwd)/ltsh_config/typedb"
```

Keep the cloned `ltsh` checkout in place after `cargo install --path ...`: upstream `ltsh` resolves `gettype.sh` relative to the cloned source tree at runtime.

For a fair baseline comparison, `ltsh_config/typedb` preserves the original upstream `ltsh` entries and adds RT simple types on top. In `src/stream/config/config.yaml`, `shellcheck_command`, `ltsh_command`, and `ltsh_typedb_path` control those external tool paths.

If you prefer macOS or another platform, install `shellcheck` and Rust through your platform package manager, make sure a Java runtime is available, then use the same `git clone`, `cp`, `cargo install`, and `export TYPEDB=...` steps.

To reproduce the main RT results and regenerate the paper artifacts, run:

```bash
bash scripts/reproduce_full.sh
```

To force regeneration even when cached outputs already exist:

```bash
bash scripts/reproduce_full.sh --force
```

That wrapper drives the baseline files, the RT runs and ablations, the merged summary CSVs, and the PDFs under `evaluation_results/plots/`.

The expanded guide, including artifact-available, artifact-functional, and results-reproducible instructions, is in `INSTRUCTIONS.md`.
