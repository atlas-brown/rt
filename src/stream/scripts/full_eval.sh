#!/bin/bash

if [ ! -d ./.git ] || [ ! -d ./evaluation_results ]; then
    echo Error: this script is meant to be run from the repo root
    exit 1
fi

FORCE="$1"

export PYTHONPATH=src

if [ ! -f evaluation_results/baseline.csv ] || [ ! -z "$FORCE" ]; then
    python3 src/stream/scripts/baseline.py
fi
if [ ! -f evaluation_results/ann:y_heuristic:y/evaluation_results.json ] || [ ! -z "$FORCE" ]; then
    python3 src/stream/run_evaluations.py
fi
if [ ! -f evaluation_results/ann:n_heuristic:y/evaluation_results.json ] || [ ! -z "$FORCE" ]; then
    python3 src/stream/run_evaluations.py --disable_annotation
fi
if [ ! -f evaluation_results/ann:y_heuristic:n/evaluation_results.json ] || [ ! -z "$FORCE" ]; then
    python3 src/stream/run_evaluations.py --disable_heuristics
fi
if [ ! -f evaluation_results/ann:n_heuristic:n/evaluation_results.json ] || [ ! -z "$FORCE" ]; then
    python3 src/stream/run_evaluations.py --disable_heuristics --disable_annotation
fi

for h in y n; do
    python3 src/stream/evaluation_summary.py \
	    --ann_csv evaluation_results/ann:y_heuristic:"$h"/results.csv \
	    --ann_json evaluation_results/ann:y_heuristic:"$h"/evaluation_results.json \
	    --raw_csv evaluation_results/ann:n_heuristic:"$h"/results.csv \
	    --raw_json evaluation_results/ann:n_heuristic:"$h"/evaluation_results.json \
	    --baseline_csv evaluation_results/baseline.csv \
	    --merged_csv evaluation_results/merged_results_heuristic:"$h".csv \
	    --bug_detection_csv evaluation_results/bug_detection_heuristic:"$h".csv \
	    --overview_csv evaluation_results/overview_heuristic:"$h".csv \
	    > evaluation_results/bug_detection_categories_heuristic:"$h".txt
done

python3 src/stream/scripts/performance.py
python3 src/stream/scripts/extract_automata_size.py

python3 src/stream/scripts/plots.py evaluation_results/overview_heuristic:y.csv evaluation_results/bug_detection_heuristic:y.csv evaluation_results/ann:y_heuristic:y/length_time_pairs.csv evaluation_results/ann:y_heuristic:y/automata_sizes.csv --output_dir evaluation_results/plots/

