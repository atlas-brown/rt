# Overview

This artifact contains the RT prototype for statically checking shell pipelines, the benchmark suites used in the evaluation, and the scripts used to regenerate the paper artifacts.

The paper makes the following claims that this artifact is designed to support:

1. **Regular types**: the artifact implements RT as an overlay type system for stream contents and the commands operating on them, together with an efficient type-checking path that detects shell-pipeline composition errors before execution (§3).
2. **Regular language operators**: the artifact implements RT's extended regular-language machinery for common input-output transformations, including finite-state-transduction support used to improve expressiveness and precision on real shell programs (§4).
3. **Extensions and optimizations**: the artifact includes RT's precision-oriented extensions and optimizations, including environment concretization, optional annotations, and heuristics, and reproduces their measured impact on accuracy, false negatives, and throughput across the benchmark suites (§5).

This artifact targets the following badges:

* [ ] [Artifact available](#artifact-available): reviewers confirm that the code, scripts, and benchmark materials are present and publicly hosted. (about 10 minutes)
* [ ] [Artifact functional](#artifact-functional): reviewers confirm that the checker runs, the test suite executes, and the main components are documented. (about 10 minutes)
* [ ] [Results reproducible](#results-reproducible): reviewers confirm the main evaluation outputs and plots reported by the artifact. (about 1 hour)

<a id="artifact-available"></a>
# Artifact Available (10 minutes)

Confirm that the repository, benchmark corpora, and experiment scripts are available:

1. The artifact code is available in this repository root; start from [README.md](README.md) and [INSTRUCTIONS.md](INSTRUCTIONS.md).
2. The repository contains the checker implementation under [`src/stream/`](src/stream/).
3. The repository contains small smoke-test inputs under [`evaluation_pipelines/`](evaluation_pipelines/).
4. The repository contains larger benchmark suites under [`full_benchmark/`](full_benchmark/).
5. The repository contains experiment scripts and checked-in outputs under [`src/stream/scripts/`](src/stream/scripts/) and [`evaluation_results/`](evaluation_results/).

<a id="artifact-functional"></a>
# Artifact Functional (10 minutes)

Confirm sufficient documentation, key components, and basic executability:

* Documentation: the top-level [README.md](README.md) provides the required artifact-facing quick-start instructions, and [INSTRUCTIONS.md](INSTRUCTIONS.md) provides the complete runbook for evaluation and reproduction.
* Key components: the type-checker and evaluation pipeline live in [`src/stream/`](src/stream/).
* Exercisability: the quickstart below checks one known-valid example, one known-invalid example, and the unit test suite.

**Quickstart: running the checker and test suite**

The recommended quickstart path is the provided Docker image.

Requirements for the quickstart:
1. Docker

From the repository root, build the container and start a shell in it:

```sh
docker build -t rt-artifact .
docker run --rm -it -v "$(pwd):/home/StreamTypes" rt-artifact
```

Inside the container, run the basic functionality checks:

```sh
bash scripts/check_functionality.sh
```

If you prefer not to use Docker, see [Optional: local host installation](#optional-local-host-installation) below.

This test suite should complete with all tests passing.

<a id="optional-local-host-installation"></a>
## Optional: local host installation

The Docker image above is the shortest path for the artifact-functional checks. If you want to install the artifact directly on your own machine instead, set up:

1. Python packages:

   ```sh
   python3 -m pip install -r requirements.txt
   ```

2. a working Java runtime, because the checker loads `jars/automaton.jar` through JPype

After the local setup, run the same functionality check:

```sh
bash scripts/check_functionality.sh
```

It should complete with all tests passing.

<!-- **Complete exploration:** To inspect the rest of the artifact, review the benchmark layout under [`full_benchmark/`](full_benchmark/), the configuration in [`config.yaml`](src/stream/config/config.yaml), and the checked-in outputs under [`evaluation_results/`](evaluation_results/). -->

<a id="results-reproducible"></a>
# Results Reproducible (about 1 hour)

The main results supported by this artifact are:

- the aggregate evaluation summaries across the configured benchmark suites,
- the ablation runs comparing annotations, heuristics, and FST reasoning,
- the timing and automata-size plots generated from the evaluation outputs.

**Preparation:**

These steps assume you already have a working environment and that the quickstart checks above succeed. The recommended path is to use the Docker image above. If you run locally instead, start with the optional host-installation steps above, then add the baseline-comparison dependencies below.

<a id="optional-local-host-installation-repro"></a>
## Optional: local host installation for the full paper pipeline

If you are not using Docker for the full paper pipeline, additionally install:

1. `shellcheck`:

   ```sh
   sudo apt-get install shellcheck
   ```

2. Rust toolchain for building `ltsh`:

   ```sh
   sudo apt-get install cargo rustc
   ```

3. upstream `ltsh`, with this repository's typedb replacing the upstream one:

   ```sh
   git clone --depth 1 --branch dev https://github.com/michaelsippel/ltsh "$HOME/.local/src/ltsh"
   cp ltsh_config/typedb "$HOME/.local/src/ltsh/typedb"
   cargo install --path "$HOME/.local/src/ltsh"
   export TYPEDB="$(pwd)/ltsh_config/typedb"
   ```

Keep the cloned `ltsh` checkout in place after `cargo install --path ...`: upstream `ltsh` resolves `gettype.sh` relative to the cloned source tree at runtime.

If you prefer macOS or another platform, install `shellcheck` and Rust through your platform package manager, make sure a Java runtime is available, then use the same `git clone`, `cp`, `cargo install`, and `export TYPEDB=...` steps.

The benchmark directories and output paths are configured in [`src/stream/config/config.yaml`](src/stream/config/config.yaml).

The baseline comparison uses `shellcheck` plus upstream `ltsh` with this repository's `ltsh_config/typedb`. For a fair comparison, `ltsh_config/typedb` preserves the original upstream `ltsh` entries and adds RT simple types on top. In [`src/stream/config/config.yaml`](src/stream/config/config.yaml), `shellcheck_command`, `ltsh_command`, and `ltsh_typedb_path` control those external tool paths.

**Full evaluation pipeline:**

To reproduce the full artifact pipeline, including the main configuration, the ablations, baseline comparison, and plot generation, run:

```sh
bash scripts/reproduce_full.sh --force
```

This wrapper calls the existing end-to-end pipeline and performs the following:

1. generates baseline data with `python3 src/stream/scripts/baseline.py`,
2. runs the main RT configuration and the ablations,
3. merges results with `python3 src/stream/evaluation_summary.py`,
4. computes timing summaries with `python3 src/stream/scripts/performance.py`,
5. regenerates the paper plots with `python3 src/stream/scripts/plots.py`.

The main configuration and ablations generated by this pipeline include:

1. `evaluation_results/ann:y_heuristic:y_fst:y/evaluation_results.json`
2. `evaluation_results/ann:n_heuristic:y_fst:y/evaluation_results.json`
3. `evaluation_results/ann:y_heuristic:n_fst:y/evaluation_results.json`
4. `evaluation_results/ann:n_heuristic:n_fst:y/evaluation_results.json`
5. `evaluation_results/ann:y_heuristic:y_fst:n/evaluation_results.json`
6. `evaluation_results/ann:n_heuristic:y_fst:n/evaluation_results.json`
7. `evaluation_results/ann:y_heuristic:n_fst:n/evaluation_results.json`
8. `evaluation_results/ann:n_heuristic:n_fst:n/evaluation_results.json`
9. `evaluation_results/ann:y_heuristic:y_fst:y_concretization:n/evaluation_results.json`
10. `evaluation_results/ann:n_heuristic:y_fst:y_concretization:n/evaluation_results.json`

The final outputs to inspect are:

1. `evaluation_results/baseline.csv`
2. `evaluation_results/baseline.json`
3. `evaluation_results/merged_results_heuristic:y_fst:y.csv`
4. `evaluation_results/bug_detection_heuristic:y_fst:y.csv`
5. `evaluation_results/overview_heuristic:y_fst:y.csv`
6. `evaluation_results/analysis_time_stats_fst:y.csv`
7. `evaluation_results/ablation_table.md`
8. `evaluation_results/timing_table.md`
9. `evaluation_results/plots/accuracy-chart-with-annotations.pdf`
10. `evaluation_results/plots/accuracy-chart-without-annotations.pdf`
11. `evaluation_results/plots/bug-detection.pdf`
12. `evaluation_results/plots/automata-sizes.pdf`

The bug-detection plot compares the unannotated RT run against ShellCheck and LadderTypes. The plot labels that system as `RT`.

If reviewers do not want to wait for the full pipeline, they can inspect the checked-in outputs already present under [`evaluation_results/`](evaluation_results/) and compare those files to regenerated outputs.

**Cleanup:**

This artifact does not require a special cleanup script. If you used Docker, exit the container. If you ran locally, you can remove any temporary output directories you created under `evaluation_results/`.
