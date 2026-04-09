# Overview

This artifact contains the RT prototype for statically checking shell pipelines, the benchmark suites used in the evaluation, and the scripts used to regenerate the paper artifacts.

The paper makes the following high-level claims that this artifact is designed to support:

1. **A shell-pipeline checker with stream-type reasoning**: the paper presents a system for analyzing shell pipelines using regular-language-based types, command models, and optional user annotations.
2. **A practical implementation with multiple analysis modes**: the artifact includes the main checker, annotation support, heuristic checks, and an FST-backed reasoning path.
3. **An empirical evaluation over multiple benchmark suites**: the artifact includes handwritten examples, curated buggy/correct corpora, and scripts for reproducing the aggregate evaluation summaries and plots.

This artifact targets the following badges:

* [ ] [Artifact available](#artifact-available): reviewers confirm that the code, scripts, and benchmark materials are present and publicly hosted.
* [ ] [Artifact functional](#artifact-functional): reviewers confirm that the checker runs, the test suite executes, and the main components are documented.
* [ ] [Results reproducible](#results-reproducible): reviewers confirm the main evaluation outputs and plots reported by the artifact.

<a id="artifact-available"></a>
# Artifact Available (10 minutes)

Confirm that the repository, benchmark corpora, and experiment scripts are available:

1. The artifact code is hosted on GitHub at [brown-cs2952r/StreamTypes](https://github.com/brown-cs2952r/StreamTypes).
2. The repository contains the checker implementation under [`src/stream/`](/home/infinite/Workspace/atlas/StreamTypes/src/stream).
3. The repository contains small smoke-test inputs under [`evaluation_pipelines/`](/home/infinite/Workspace/atlas/StreamTypes/evaluation_pipelines).
4. The repository contains larger benchmark suites under [`full_benchmark/`](/home/infinite/Workspace/atlas/StreamTypes/full_benchmark).
5. The repository contains experiment scripts and checked-in outputs under [`src/stream/scripts/`](/home/infinite/Workspace/atlas/StreamTypes/src/stream/scripts) and [`evaluation_results/`](/home/infinite/Workspace/atlas/StreamTypes/evaluation_results).

In particular, the artifact package includes:

- the top-level [README.md](/home/infinite/Workspace/atlas/StreamTypes/README.md),
- this [INSTRUCTIONS.md](/home/infinite/Workspace/atlas/StreamTypes/INSTRUCTIONS.md),
- the single-pipeline checker wrapper [typecheck.sh](/home/infinite/Workspace/atlas/StreamTypes/typecheck.sh),
- the batch evaluation wrapper [run_evaluations.sh](/home/infinite/Workspace/atlas/StreamTypes/run_evaluations.sh),
- the test runner [run_tests.sh](/home/infinite/Workspace/atlas/StreamTypes/run_tests.sh),
- the end-to-end evaluation script [full_eval.sh](/home/infinite/Workspace/atlas/StreamTypes/src/stream/scripts/full_eval.sh).

<a id="artifact-functional"></a>
# Artifact Functional (20 minutes)

Confirm sufficient documentation, key components, and basic executability:

* Documentation: the top-level [README.md](/home/infinite/Workspace/atlas/StreamTypes/README.md) provides the required artifact-facing quick-start instructions, and [INSTRUCTIONS.md](/home/infinite/Workspace/atlas/StreamTypes/INSTRUCTIONS.md) provides the complete runbook for evaluation and reproduction.
* Key components: the checker and evaluation pipeline live in [`src/stream/`](/home/infinite/Workspace/atlas/StreamTypes/src/stream), especially [debug.py](/home/infinite/Workspace/atlas/StreamTypes/src/stream/debug.py), [run_evaluations.py](/home/infinite/Workspace/atlas/StreamTypes/src/stream/run_evaluations.py), [evaluation_summary.py](/home/infinite/Workspace/atlas/StreamTypes/src/stream/evaluation_summary.py), and the scripts under [`src/stream/scripts/`](/home/infinite/Workspace/atlas/StreamTypes/src/stream/scripts).
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
sh typecheck.sh -f evaluation_pipelines/valid/3.sh
sh typecheck.sh -f evaluation_pipelines/invalid/3.sh
sh run_tests.sh -q
```

Optional annotation-focused smoke test:

```sh
sh typecheck.sh -f dummy_example.sh
```

These commands exercise:

1. the single-pipeline checker path,
2. the core command-model and type-checking logic,
3. the regression test suite under `src/stream/unit_tests/`.

**Complete exploration:** To inspect the rest of the artifact, review the benchmark layout under [`full_benchmark/`](/home/infinite/Workspace/atlas/StreamTypes/full_benchmark), the configuration in [`config.yaml`](/home/infinite/Workspace/atlas/StreamTypes/src/stream/config/config.yaml), and the checked-in outputs under [`evaluation_results/`](/home/infinite/Workspace/atlas/StreamTypes/evaluation_results).

<a id="results-reproducible"></a>
# Results Reproducible (about 5 hours)

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

The benchmark directories and output paths are configured in [`src/stream/config/config.yaml`](/home/infinite/Workspace/atlas/StreamTypes/src/stream/config/config.yaml).

**Main evaluation:**

To reproduce the main configuration used by the checked-in outputs, run:

```sh
./run_evaluations.sh --outdir evaluation_results/ann:y_heuristic:y_fst:y
```

This writes:

1. `evaluation_results/ann:y_heuristic:y_fst:y/evaluation_results.json`
2. `evaluation_results/ann:y_heuristic:y_fst:y/summary.csv`
3. `evaluation_results/ann:y_heuristic:y_fst:y/automata_sizes.csv`
4. `evaluation_results/ann:y_heuristic:y_fst:y/length_time_pairs.csv`

**Ablations:**

To reproduce the major ablations, run:

```sh
# annotations disabled
./run_evaluations.sh --disable_annotation --outdir evaluation_results/ann:n_heuristic:y_fst:y

# heuristics disabled
./run_evaluations.sh --disable_rule_no_empty_output \
  --disable_rule_no_ignored_input \
  --disable_rule_no_meaningless_command \
  --disable_rule_no_sort_non_numeric_with_numeric_input \
  --outdir evaluation_results/ann:y_heuristic:n_fst:y

# FST reasoning disabled
./run_evaluations.sh --disable_fsts --outdir evaluation_results/ann:y_heuristic:y_fst:n

# annotations disabled and FST reasoning disabled
./run_evaluations.sh --disable_annotation --disable_fsts \
  --outdir evaluation_results/ann:n_heuristic:y_fst:n
```

**Full evaluation pipeline:**

To reproduce the full artifact pipeline, including baseline comparison and plot generation, run:

```sh
bash src/stream/scripts/full_eval.sh
```

To force regeneration even when outputs already exist:

```sh
bash src/stream/scripts/full_eval.sh force
```

This script performs the following:

1. generates baseline data with `python3 src/stream/scripts/baseline.py`,
2. runs the main StreamTypes configuration and the ablations,
3. merges results with `python3 src/stream/evaluation_summary.py`,
4. computes timing summaries with `python3 src/stream/scripts/performance.py`,
5. regenerates the paper plots with `python3 src/stream/scripts/plots.py`.

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

If reviewers do not want to wait for the full pipeline, they can inspect the checked-in outputs already present under [`evaluation_results/`](/home/infinite/Workspace/atlas/StreamTypes/evaluation_results) and compare those files to regenerated outputs.

**Cleanup:**

This artifact does not require a special cleanup script. If you used Docker, exit the container. If you ran locally, you can remove any temporary output directories you created under `evaluation_results/`.
