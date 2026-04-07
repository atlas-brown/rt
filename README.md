# RT

This artifact packages the RT prototype, the benchmark corpora used by the paper, and the scripts needed to run the checker, execute the benchmark suite, and regenerate summary outputs. The shortest path through the artifact is:

1. set up the environment,
2. run the checker on one known-valid and one known-invalid pipeline,
3. run the unit tests.

The full replication path is:

1. generate baseline results against external tools,
2. run the RT configurations and ablations,
3. merge the results,
4. regenerate the paper plots.

## Getting Started Instructions

### 1. Prepare the environment

Use either Docker or a local Python/Java environment from the repository root.

Docker:

```bash
docker build -t rt .
docker run --rm -it -v "$(pwd):/home/RT" rt
```

Local:

```bash
python3 -m pip install -r requirements.txt
```

The checker uses JPype to load the automata implementation from `jars/automaton.jar`, so the local path also needs a working Java runtime. The Docker image already installs Python and Java.

### 2. Run a quick smoke test on small examples

These commands exercise the checker on two tiny labeled examples that ship with the artifact. They only analyze the pipelines; they do not execute `curl`, `sed`, `wc`, or any other shell command appearing inside the pipeline text.

Known-valid example:

```bash
sh typecheck.sh -f evaluation_pipelines/valid/3.sh
```

Known-invalid example:

```bash
sh typecheck.sh -f evaluation_pipelines/invalid/3.sh
```

You can also check a pipeline from standard input:

```bash
printf 'seq 1 3 | wc -l\n' | sh typecheck.sh -s
```

If you want an annotation-focused example, inspect `dummy_example.sh` and then run:

```bash
sh typecheck.sh -f dummy_example.sh
```

### 3. Run the unit tests

```bash
sh run_tests.sh -q
```

The test suite lives under `src/stream/unit_tests/` and excludes the large benchmark corpora under `full_benchmark/`.

### 4. What to inspect next

- `src/stream/config/config.yaml` controls the default benchmark directories, logging, timeout behavior, and output locations.
- `evaluation_pipelines/` contains small hand-checkable examples.
- `full_benchmark/` contains the larger benchmark sets used for experiments.
- `evaluation_results/` contains checked-in outputs and regenerated experiment artifacts.

## Detailed Instructions

### Artifact layout

- `src/stream/`: core implementation of the parser, command models, transducers, checker, evaluation driver, and post-processing scripts.
- `evaluation_pipelines/`: small valid/invalid examples for quick testing.
- `full_benchmark/`: larger corpora used in the evaluation, including Koala, StackOverflow, InterCode, GitHub commits, curated mutants, PaSh, and LLM-injection pipelines.
- `evaluation_results/`: output directory for JSON summaries, CSV tables, and paper plots.
- `src/stream/evaluation_notes.json`: benchmark metadata used to categorize and explain findings.

The structure here is similar in spirit to the Koala `INSTRUCTIONS.md` file: start from the runnable entry points, explain the directory layout, and then document the full experiment path. The difference is that RT is an executable checker plus evaluation scripts, not a benchmark harness, so the README focuses on running the checker and reproducing the paper outputs rather than on per-benchmark setup scripts.

### Core entry points

Single-pipeline checking:

```bash
sh typecheck.sh -f path/to/pipeline.sh
sh typecheck.sh -s
```

Batch evaluation over the configured benchmark directories:

```bash
./run_evaluations.sh
```

Unit tests:

```bash
sh run_tests.sh
```

The `run_evaluations.sh` wrapper forwards directly to `src/stream/run_evaluations.py`. The most important flags are:

- `--disable_annotation`: disable user annotations.
- `--disable_fsts`: disable FST-based reasoning.
- `--disable_rule_no_empty_output`
- `--disable_rule_no_ignored_input`
- `--disable_rule_no_meaningless_command`
- `--disable_rule_no_sort_non_numeric_with_numeric_input`
- `--workers N`: number of parallel workers.
- `--timeout SEC`: per-pipeline timeout; use `0` to disable.
- `--log_level INFO|DEBUG|ERROR`
- `--outdir DIR`: write outputs to `DIR` using the standard file names.

Each direct evaluation run writes these files into the selected output directory:

- `evaluation_results.json`: full per-pipeline results plus aggregate statistics.
- `summary.csv`: human-readable summary table.
- `automata_sizes.csv`: automata-size statistics extracted from the run.
- `length_time_pairs.csv`: per-pipeline length/time data.

### Reproducing the main evaluation results

The benchmark directories used by default are listed in `src/stream/config/config.yaml` under `valid_dirs`, `invalid_dirs`, and `not_check_all_dirs`. To reproduce the paper runs exactly, keep those settings unchanged and execute the top-level evaluation script from the repository root.

Main configuration with annotations and FSTs enabled:

```bash
./run_evaluations.sh --outdir evaluation_results/ann:y_heuristic:y_fst:y
```

Important ablations:

```bash
./run_evaluations.sh --disable_annotation --outdir evaluation_results/ann:n_heuristic:y_fst:y
./run_evaluations.sh --disable_rule_no_empty_output \
  --disable_rule_no_ignored_input \
  --disable_rule_no_meaningless_command \
  --disable_rule_no_sort_non_numeric_with_numeric_input \
  --outdir evaluation_results/ann:y_heuristic:n_fst:y
./run_evaluations.sh --disable_fsts --outdir evaluation_results/ann:y_heuristic:y_fst:n
./run_evaluations.sh --disable_annotation --disable_fsts \
  --outdir evaluation_results/ann:n_heuristic:y_fst:n
```

These directory names match the convention already used in the checked-in results:

- `ann:y|n`: annotations enabled or disabled
- `heuristic:y|n`: heuristics enabled or disabled
- `fst:y|n`: FST reasoning enabled or disabled

### Reproducing baseline comparisons and the paper plots

The full paper pipeline needs a few tools that are not required for the quick smoke test:

- `shellcheck` in `PATH`
- `ltsh` in `PATH`
- plotting packages: `pandas`, `numpy`, `matplotlib`, and `matplotlib-set-diagrams`

After those are available, the simplest end-to-end reproduction command is:

```bash
bash src/stream/scripts/full_eval.sh
```

To force recomputation even when output files already exist:

```bash
bash src/stream/scripts/full_eval.sh force
```

This script performs the full experiment pipeline:

1. generates the baseline comparison files with `python3 src/stream/scripts/baseline.py`,
2. runs the main RT configuration and the ablations,
3. merges annotated and raw outputs with `python3 src/stream/evaluation_summary.py`,
4. computes timing summaries with `python3 src/stream/scripts/performance.py`,
5. regenerates paper plots with `python3 src/stream/scripts/plots.py`.

The main generated artifacts are:

- `evaluation_results/baseline.csv` and `evaluation_results/baseline.json`
- `evaluation_results/merged_results_heuristic:*.csv`
- `evaluation_results/bug_detection_heuristic:*.csv`
- `evaluation_results/overview_heuristic:*.csv`
- `evaluation_results/analysis_time_stats_fst:*.csv`
- `evaluation_results/plots/accuracy-chart.pdf`
- `evaluation_results/plots/bug-detection.pdf`
- `evaluation_results/plots/time-length-chart.pdf`
- `evaluation_results/plots/automata-sizes.pdf`

If you want to rerun only individual post-processing steps, use the commands embedded in `src/stream/scripts/full_eval.sh` as the ground truth for the paper pipeline.

### Annotation-aware experiments

RT supports inline user annotations. A small example is:

```bash
# @assume "cat $1" --> ".*\t.*"
# @output "[^ ]+"
cat $1 | cut -f 2 | sort -n | uniq -c | sort -nr | head -n 1
```

The annotation forms used by the artifact are:

- `@assume`: assume an output type for a command.
- `@assert`: require the inferred output type to be a subset of a given language.
- `@expect`: specify the expected input type of a command.
- `@input`: specify the type of the whole pipeline input stream.
- `@output`: specify the expected type of the whole pipeline output stream.
- `@file`: specify the type of a referenced file.

For the GitHub-commit benchmark, search for `# stream enable` under `full_benchmark/github_repos_commits/output_new`. If a change is outside the annotation scope, remove that marker. If a change is in scope, replace `# put stream annotation here` with the needed user annotations.

### Practical notes

- `typecheck.sh` is a thin wrapper around `src/stream/debug.py`.
- `run_tests.sh` runs `pytest` with `PYTHONPATH=src`.
- `run_evaluations.sh` clears `evaluation_results/parsing_errors.log` before each batch run.
- Large batch runs traverse the full benchmark sets listed in `config.yaml`; use the quick-start commands above when you only want a functional smoke test.
- If you only want to inspect the artifact without rerunning everything, the repository already contains representative outputs under `evaluation_results/`.
