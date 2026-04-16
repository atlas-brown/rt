# RT

## Artifact evaluation
To evaluate the artifact for the OSDI'26 paper titled "RT: Regular Types for the Streaming Shell", jump straight to [INSTRUCTIONS.md](INSTRUCTIONS.md).

RT is a prototype for statically checking shell pipelines with stream-type reasoning, command models, and optional user annotations. This repository includes the checker implementation, the benchmark suites used in the evaluation, and the scripts used to regenerate the reported outputs.

The root `README.md` is the short artifact-facing entry point. The fuller artifact-evaluation flow, including badge-oriented instructions and the longer reproduction path, is in `INSTRUCTIONS.md`.

## Getting Started Instructions

The fastest way to validate the artifact is to build the container or install the Python dependencies locally and then run the functionality-check wrapper script.

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
bash scripts/check_functionality.sh
```

These commands should be enough for a basic functionality check in well under 30 minutes. For the badge-oriented evaluation flow and the longer reproduction path, see `INSTRUCTIONS.md`.

## Detailed Instructions

The main entry points are:

- `bash scripts/check_functionality.sh` for the artifact-functional path,
- `bash scripts/reproduce_full.sh` for the full paper pipeline,
- `sh typecheck.sh -f <pipeline-file>` for ad hoc single-pipeline checking,
- `./run_evaluations.sh` for ad hoc batch evaluation over the configured corpora.

The benchmark directories used by the batch runner are configured in `src/stream/config/config.yaml`. By default they include the small handwritten examples in `evaluation_pipelines/` plus the larger corpora in `full_benchmark/`.

To reproduce the main RT results and regenerate the paper artifacts, run:

```bash
bash scripts/reproduce_full.sh
```

To force regeneration even when cached outputs already exist:

```bash
bash scripts/reproduce_full.sh --force
```

For the full experiment pipeline, including baseline comparison and plot regeneration, install the extra tools required by the scripts:

- `shellcheck`
- `ltsh`
- plotting packages such as `pandas`, `numpy`, `matplotlib`, and `matplotlib-set-diagrams`

That wrapper drives the baseline files, the RT runs and ablations, the merged summary CSVs, and the PDFs under `evaluation_results/plots/`.

The expanded guide, including artifact-available, artifact-functional, and results-reproducible instructions, is in `INSTRUCTIONS.md`.
