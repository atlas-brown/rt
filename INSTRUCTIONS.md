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

1. The artifact code is hosted on GitHub at [brown-cs2952r/StreamTypes](https://github.com/brown-cs2952r/StreamTypes).
2. The repository contains the checker implementation under [`src/stream/`](src/stream/).
3. The repository contains small smoke-test inputs under [`evaluation_pipelines/`](evaluation_pipelines/).
4. The repository contains larger benchmark suites under [`full_benchmark/`](full_benchmark/).
5. The repository contains experiment scripts and checked-in outputs under [`src/stream/scripts/`](src/stream/scripts/) and [`evaluation_results/`](evaluation_results/).

<!-- In particular, the artifact package includes:

- the top-level [README.md](README.md),
- this [INSTRUCTIONS.md](INSTRUCTIONS.md),
- the artifact-functional wrapper [check_functionality.sh](scripts/check_functionality.sh),
- the full reproduction wrapper [reproduce_full.sh](scripts/reproduce_full.sh),
- the single-pipeline checker wrapper [typecheck.sh](typecheck.sh),
- the batch evaluation wrapper [run_evaluations.sh](run_evaluations.sh),
- the test runner [run_tests.sh](run_tests.sh),
- the end-to-end evaluation script [full_eval.sh](src/stream/scripts/full_eval.sh). -->

<a id="artifact-functional"></a>
# Artifact Functional (10 minutes)

Confirm sufficient documentation, key components, and basic executability:

* Documentation: the top-level [README.md](README.md) provides the required artifact-facing quick-start instructions, and [INSTRUCTIONS.md](INSTRUCTIONS.md) provides the complete runbook for evaluation and reproduction.
* Key components: the type-checker and evaluation pipeline live in [`src/stream/`](src/stream/).
* Exercisability: the quickstart below checks one known-valid example, one known-invalid example, and the unit test suite.

**Quickstart: running the checker and test suite**

You can use either Docker or a local Python/Java environment.

Requirements for the quickstart:
1. Docker, or
2. Python 3 plus a working Java runtime

From the repository root, either build the container:

```sh
docker build -t streamtypes-ae .
docker run --rm -it -v "$(pwd):/home/StreamTypes" streamtypes-ae
```

or install the base Python dependencies locally:

```sh
python3 -m pip install -r requirements.txt
```

The local path also needs Java because the checker loads `jars/automaton.jar` through JPype.

Then run the basic functionality checks:

```sh
bash scripts/check_functionality.sh
```

This script exercises:

1. the single-pipeline checker path,
2. the core command-model and type-checking logic,
3. the regression test suite under `src/stream/unit_tests/`.

By default it also runs the annotation-focused example `dummy_example.sh`. If needed, you can skip that part with:

```sh
RT_SKIP_ANNOTATION_CHECK=1 bash scripts/check_functionality.sh
```

**Complete exploration:** To inspect the rest of the artifact, review the benchmark layout under [`full_benchmark/`](full_benchmark/), the configuration in [`config.yaml`](src/stream/config/config.yaml), and the checked-in outputs under [`evaluation_results/`](evaluation_results/).

<a id="results-reproducible"></a>
# Results Reproducible (about 1 hour)

The main results supported by this artifact are:

- the aggregate evaluation summaries across the configured benchmark suites,
- the ablation runs comparing annotations, heuristics, and FST reasoning,
- the timing and automata-size plots generated from the evaluation outputs.

**Preparation:**

These steps assume you already have a working Docker container or local environment and that the quickstart checks above succeed.

For the full paper pipeline, the scripts additionally expect:

- `shellcheck`
- `ltsh`
- `pandas`
- `numpy`
- `matplotlib`
- `matplotlib-set-diagrams`

The benchmark directories and output paths are configured in [`src/stream/config/config.yaml`](src/stream/config/config.yaml).

**Full evaluation pipeline:**

To reproduce the full artifact pipeline, including the main configuration, the ablations, baseline comparison, and plot generation, run:

```sh
bash scripts/reproduce_full.sh
```

To force regeneration even when outputs already exist:

```sh
bash scripts/reproduce_full.sh --force
```

This wrapper calls the existing end-to-end pipeline and performs the following:

1. generates baseline data with `python3 src/stream/scripts/baseline.py`,
2. runs the main StreamTypes configuration and the ablations,
3. merges results with `python3 src/stream/evaluation_summary.py`,
4. computes timing summaries with `python3 src/stream/scripts/performance.py`,
5. regenerates the paper plots with `python3 src/stream/scripts/plots.py`.

The main configuration and ablations generated by this pipeline include:

1. `evaluation_results/ann:y_heuristic:y_fst:y/evaluation_results.json`
2. `evaluation_results/ann:n_heuristic:y_fst:y/evaluation_results.json`
3. `evaluation_results/ann:y_heuristic:n_fst:y/evaluation_results.json`
4. `evaluation_results/ann:y_heuristic:y_fst:n/evaluation_results.json`
5. `evaluation_results/ann:n_heuristic:y_fst:n/evaluation_results.json`

The final outputs to inspect are:

1. `evaluation_results/baseline.csv`
2. `evaluation_results/baseline.json`
3. `evaluation_results/merged_results_heuristic:y_fst:y.csv`
4. `evaluation_results/bug_detection_heuristic:y_fst:y.csv`
5. `evaluation_results/overview_heuristic:y_fst:y.csv`
6. `evaluation_results/analysis_time_stats_fst:y.csv`
7. `evaluation_results/plots/accuracy-chart.pdf`
8. `evaluation_results/plots/bug-detection.pdf`
9. `evaluation_results/plots/time-length-chart.pdf`
10. `evaluation_results/plots/automata-sizes.pdf`

If reviewers do not want to wait for the full pipeline, they can inspect the checked-in outputs already present under [`evaluation_results/`](evaluation_results/) and compare those files to regenerated outputs.

**Cleanup:**

This artifact does not require a special cleanup script. If you used Docker, exit the container. If you ran locally, you can remove any temporary output directories you created under `evaluation_results/`.
