# RT

To evaluate the artifact for the OSDI'26 paper titled "RT: Regular Types for the Streaming Shell", jump straight to [INSTRUCTIONS.md](INSTRUCTIONS.md).

## Getting Started Instructions

RT is a prototype for statically checking shell pipelines with regular types, command models, finite-state transducers, and optional user annotations. This artifact includes the checker implementation, the benchmark suites used in the paper evaluation for functional checks and result reproduction.

The fastest way to check the basic functionality is to use the provided Docker image. From the repository root, build the image and start a shell in it:

```sh
docker build -t rt-artifact .
docker run --rm -it -v "$(pwd):/home/StreamTypes" rt-artifact
```

Inside the container, run:

```sh
bash scripts/check_functionality.sh
```

This script runs the unit test suite and then runs RT on `examples/motivating_example.sh` through the top-level `rt.sh` entry point. The smoke test should print the first expected RT diagnostic for the motivating example. This is the short artifact-functional path and should complete within the short review window.

For local host installation instead of Docker, install the Python requirements and a Java runtime before running the same command.

## Detailed Instructions

The main entry points are:

1. `bash scripts/check_functionality.sh` for the short functionality check.
2. `bash scripts/reproduce_full.sh --force` for the full paper-result reproduction.

The full reproduction pipeline runs the baseline comparison, the main RT configuration, the ablations, and the plot/table generation. Its runtime depends on the machine and storage speed; on a typical review machine, expect roughly one hour.

The primary outputs to inspect after full reproduction are:

1. `evaluation_results/tables/ablation_table.md`
2. `evaluation_results/tables/timing_table.md`
3. `evaluation_results/plots/accuracy-chart-with-annotations.pdf`
4. `evaluation_results/plots/accuracy-chart-without-annotations.pdf`
5. `evaluation_results/plots/bug-detection.pdf`
6. `evaluation_results/plots/automata-sizes.pdf`

The benchmark directories and output paths are configured in `src/stream/config/config.yaml`. For local non-Docker reproduction, make sure Python, Java, ShellCheck, Rust, and LadderTypes are available before running the full pipeline.
