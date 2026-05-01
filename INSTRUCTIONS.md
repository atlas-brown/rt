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

1. The top-level RT entry point is [`rt.sh`](rt.sh). It runs the checker on a shell script.
2. The checker implementation is under [`src/stream/`](src/stream/), with the technical contributions mapped as follows:
   * Regular types: [`src/stream/regular_type.py`](src/stream/regular_type.py), [`src/stream/command_type.py`](src/stream/command_type.py).
   * Type database: [`src/stream/signatures/`](src/stream/signatures/), [`src/stream/special_signatures/`](src/stream/special_signatures/), [`src/stream/command_signature.py`](src/stream/command_signature.py).
   * Typechecker: [`src/stream/type_checker.py`](src/stream/type_checker.py).
   * Regular-language operators and transducers: [`src/stream/regular_operator.py`](src/stream/regular_operator.py), [`src/stream/transducer.py`](src/stream/transducer.py), [`src/stream/transducer_utils.py`](src/stream/transducer_utils.py).
3. The large benchmark suites are under [`full_benchmark/`](full_benchmark/).
4. The experiment scripts and checked-in outputs are under [`src/stream/scripts/`](src/stream/scripts/) and [`evaluation_results/`](evaluation_results/).

<a id="artifact-functional"></a>
# Artifact Functional (10 minutes)

Confirm sufficient documentation, key components, and basic executability:

* Documentation: the top-level [README.md](README.md) provides the required artifact-facing quick-start instructions, and [INSTRUCTIONS.md](INSTRUCTIONS.md) provides the complete runbook for evaluation and reproduction.
* Key components: the type-checker and evaluation pipeline live in [`src/stream/`](src/stream/).
* Exercisability: the quickstart below runs the unit test suite and one RT smoke test.

**Quickstart: running the test suite and smoke test**

The recommended quickstart path is the provided Docker image.

From the repository root, build the container and start a shell in it:

```sh
docker build -t rt-artifact .
docker run --rm -it -v "$(pwd):/home/StreamTypes" rt-artifact
```

Inside the container, run the basic functionality checks:

```sh
bash scripts/check_functionality.sh
```

If you prefer not to use Docker, see [Optional local host installation](#optional-local-host-installation).

This script should complete with all unit tests passing, then run RT on the paper motivating example and print the first expected RT diagnostic.

```text
Running smoke tests: bash rt.sh examples/motivating_example.sh
Error (ln. 2):
> grep -E "book[0-9]+\.txt" | xargs cat | ...
  grep -E "book[0-9]+\.txt" > (\.(/.+)?)&(((.*)(book[0-9]+\.txt))(.*))
maybe incompatible w/
  xargs cat > [^[:blank:]]+|".+"|'.+'
Counterexample: "./\tbook0.txt"
```

<!-- **Complete exploration:** To inspect the rest of the artifact, review the benchmark layout under [`full_benchmark/`](full_benchmark/), the configuration in [`config.yaml`](src/stream/config/config.yaml), and the checked-in outputs under [`evaluation_results/`](evaluation_results/). -->

<a id="results-reproducible"></a>
# Results Reproducible (about 1 hour, depending on the machine)

The main results supported by this artifact are:

- the aggregate evaluation summaries across the configured benchmark suites,
- the ablation runs comparing annotations, heuristics, and FST reasoning,
- the timing and automata-size plots generated from the evaluation outputs.

**Preparation:**

These steps assume you already have a working environment and that the quickstart checks above succeed. The recommended path is to use the Docker image above. If you run locally instead, complete [Optional local host installation](#optional-local-host-installation) before running the full pipeline.

The benchmark directories and output paths are configured in [`src/stream/config/config.yaml`](src/stream/config/config.yaml), where `shellcheck_command` and `ltsh_command` control the external tool paths.

**Full evaluation pipeline:**

To reproduce the full artifact pipeline, including the main configuration, the ablations, baseline comparison, and plot generation, run:

```sh
bash scripts/reproduce_full.sh --force
```

This wrapper calls the existing end-to-end pipeline and performs the following:

1. generates baseline data with `python3 src/stream/scripts/baseline.py`,
2. runs the main RT configuration and the ablations,
3. regenerates the paper plots with `python3 src/stream/scripts/plots.py`.

The final outputs to inspect are:

1. `evaluation_results/tables/ablation_table.md`
2. `evaluation_results/tables/timing_table.md`
3. `evaluation_results/plots/accuracy-chart-with-annotations.pdf`
4. `evaluation_results/plots/accuracy-chart-without-annotations.pdf`
5. `evaluation_results/plots/bug-detection.pdf`
6. `evaluation_results/plots/automata-sizes.pdf`

The bug-detection plot compares the RT without annotations run against ShellCheck and LadderTypes. The plot labels that system as `RT`.

If you do not want to wait for the full pipeline, you can inspect the checked-in outputs already present under [`evaluation_results/`](evaluation_results/).

**Cleanup:**

This artifact does not require a special cleanup script. If you used Docker, exit the container. If you ran locally, you can remove any temporary output directories you created under `evaluation_results/`. If you installed `ltsh`, `shellcheck`, or Python packages only for this artifact review, remove those installed packages if they are not needed, and remove the cloned `ltsh` checkout.

<a id="optional-local-host-installation"></a>
# Optional Local Host Installation

The Docker image is the shortest supported path for both badge checks. If you install the artifact directly on your own machine instead, use the following setup.

For the artifact-functional checks, install:

1. Python packages:

   ```sh
   python3 -m pip install -r requirements.txt
   ```

2. a working Java runtime, because the checker loads `jars/automaton.jar` through JPype

After this setup, run:

```sh
bash scripts/check_functionality.sh
```

For the full paper pipeline, also install:

1. `shellcheck`:

   ```sh
   sudo apt-get install shellcheck
   ```

2. Rust toolchain for building `ltsh`:

   ```sh
   sudo apt-get install cargo rustc
   ```

3. upstream `ltsh`, available on `PATH`:

   ```sh
   LTSH_CHECKOUT=/path/to/ltsh
   git clone --depth 1 --branch dev https://github.com/michaelsippel/ltsh "$LTSH_CHECKOUT"
   cargo install --path "$LTSH_CHECKOUT"
   ```

Keep the cloned `ltsh` checkout in place after `cargo install --path ...`: upstream `ltsh` resolves `gettype.sh` relative to the cloned source tree at runtime.

If you prefer macOS or another platform, install `shellcheck` and Rust through your platform package manager, make sure a Java runtime is available, then use the same `git clone` and `cargo install` steps.
