# RT

## Artifact evaluation
To evaluate the artifact, jump straight to [INSTRUCTIONS.md](/home/infinite/Workspace/atlas/StreamTypes/INSTRUCTIONS.md).

RT is a prototype for statically checking shell pipelines with stream-type reasoning, command models, and optional user annotations. This repository includes the checker implementation, the benchmark suites used in the evaluation, and the scripts used to regenerate the reported outputs.

The root `README.md` is the short artifact-facing entry point. The fuller artifact-evaluation flow, including badge-oriented instructions and the longer reproduction path, is in `INSTRUCTIONS.md`.

## Getting Started Instructions

The fastest way to validate the artifact is to build the container or install the Python dependencies locally, run the checker on one small valid pipeline and one small invalid pipeline, and then run the unit tests.

Docker path:

```bash
docker build -t rt-artifact .
docker run --rm -it -v "$(pwd):/home/StreamTypes" rt-artifact
```

Local path:

```bash
python3 -m pip install -r requirements.txt
```

The checker uses Java through JPype, so the local path also needs a working Java runtime. From the repository root, run:

```bash
sh typecheck.sh -f evaluation_pipelines/valid/3.sh
sh typecheck.sh -f evaluation_pipelines/invalid/3.sh
sh run_tests.sh -q
```

If you want one annotation-focused example as part of the smoke test, also run:

```bash
sh typecheck.sh -f dummy_example.sh
```

These commands should be enough for a basic functionality check in well under 30 minutes. For the badge-oriented evaluation flow and the longer reproduction path, see `INSTRUCTIONS.md`.

## Detailed Instructions

The main entry points are:

- `sh typecheck.sh -f <pipeline-file>` for checking one pipeline,
- `./run_evaluations.sh` for batch evaluation over the configured corpora,
- `bash src/stream/scripts/full_eval.sh` for the full paper pipeline,
- `sh run_tests.sh` for the unit tests.

The benchmark directories used by the batch runner are configured in `src/stream/config/config.yaml`. By default they include the small handwritten examples in `evaluation_pipelines/` plus the larger corpora in `full_benchmark/`.

To reproduce the main RT results, run:

```bash
./run_evaluations.sh --outdir evaluation_results/ann:y_heuristic:y_fst:y
```

Important ablations are:

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

Each evaluation run writes `evaluation_results.json`, `summary.csv`, `automata_sizes.csv`, and `length_time_pairs.csv` into the selected output directory.

For the full experiment pipeline, including baseline comparison and plot regeneration, install the extra tools required by the scripts:

- `shellcheck`
- `ltsh`
- plotting packages such as `pandas`, `numpy`, `matplotlib`, and `matplotlib-set-diagrams`

Then run:

```bash
bash src/stream/scripts/full_eval.sh
```

That script generates the baseline files, the RT runs and ablations, the merged summary CSVs, and the PDFs under `evaluation_results/plots/`.

The expanded guide, including artifact-available, artifact-functional, and results-reproducible instructions, is in `INSTRUCTIONS.md`.
