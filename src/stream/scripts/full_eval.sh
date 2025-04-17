#!/bin/bash

set -e

if [ ! -d ./.git ] || [ ! -d ./evaluation_results ]; then
    echo Error: this script is meant to be run from the repo root
    exit 1
fi

FORCE="$1"

export PYTHONPATH=src

DISABLE_HEURISTICS_FLAGS="--disable_rule_no_empty_output --disable_rule_no_ignored_input --disable_rule_no_meaningless_command --disable_rule_no_sort_non_numeric_with_numeric_input"

if [ ! -f evaluation_results/baseline.csv ] || [ ! -z "$FORCE" ]; then
    python3 src/stream/scripts/baseline.py
fi
if [ ! -f evaluation_results/ann:y_heuristic:y_fst:y/evaluation_results.json ] || [ ! -z "$FORCE" ]; then
    python3 src/stream/run_evaluations.py --outdir evaluation_results/ann:y_heuristic:y_fst:y
fi
if [ ! -f evaluation_results/ann:n_heuristic:y_fst:y/evaluation_results.json ] || [ ! -z "$FORCE" ]; then
    python3 src/stream/run_evaluations.py --disable_annotation --outdir evaluation_results/ann:n_heuristic:y_fst:y
fi
if [ ! -f evaluation_results/ann:y_heuristic:n_fst:y/evaluation_results.json ] || [ ! -z "$FORCE" ]; then
    python3 src/stream/run_evaluations.py $DISABLE_HEURISTICS_FLAGS --outdir evaluation_results/ann:y_heuristic:n_fst:y
fi
# if [ ! -f evaluation_results/ann:n_heuristic:n_fst:y/evaluation_results.json ] || [ ! -z "$FORCE" ]; then
#     python3 src/stream/run_evaluations.py $DISABLE_HEURISTICS_FLAGS --disable_annotation
# fi
if [ ! -f evaluation_results/ann:y_heuristic:y_fst:n/evaluation_results.json ] || [ ! -z "$FORCE" ]; then
    python3 src/stream/run_evaluations.py --disable_fsts --outdir evaluation_results/ann:y_heuristic:y_fst:n
fi
if [ ! -f evaluation_results/ann:n_heuristic:y_fst:n/evaluation_results.json ] || [ ! -z "$FORCE" ]; then
    python3 src/stream/run_evaluations.py --disable_annotation --disable_fsts --outdir evaluation_results/ann:n_heuristic:y_fst:n
fi

for f in y n; do
    for h in y n; do
	if [ -f evaluation_results/ann:y_heuristic:"$h"_fst:"$f"/evaluation_results.json ] && [ -f evaluation_results/ann:n_heuristic:"$h"_fst:"$f"/evaluation_results.json ]; then
	    python3 src/stream/evaluation_summary.py \
		    --ann_csv evaluation_results/ann:y_heuristic:"$h"_fst:"$f"/results.csv \
		    --ann_json evaluation_results/ann:y_heuristic:"$h"_fst:"$f"/evaluation_results.json \
		    --raw_csv evaluation_results/ann:n_heuristic:"$h"_fst:"$f"/results.csv \
		    --raw_json evaluation_results/ann:n_heuristic:"$h"_fst:"$f"/evaluation_results.json \
		    --baseline_csv evaluation_results/baseline.csv \
		    --merged_csv evaluation_results/merged_results_heuristic:"$h"_fst:"$f".csv \
		    --bug_detection_csv evaluation_results/bug_detection_heuristic:"$h"_fst:"$f".csv \
		    --overview_csv evaluation_results/overview_heuristic:"$h"_fst:"$f".csv \
		    > evaluation_results/bug_detection_categories_heuristic:"$h"_fst:"$f".txt
	fi
    done
done

python3 src/stream/scripts/performance.py evaluation_results/ann:y_heuristic:y_fst:y/evaluation_results.json evaluation_results/baseline.csv evaluation_results/ann:y_heuristic:y_fst:y/length_time_pairs.csv evaluation_results/analysis_time_stats_fst:y.csv
python3 src/stream/scripts/performance.py evaluation_results/ann:y_heuristic:y_fst:n/evaluation_results.json evaluation_results/baseline.csv evaluation_results/ann:y_heuristic:y_fst:n/length_time_pairs.csv evaluation_results/analysis_time_stats_fst:n.csv
python3 src/stream/scripts/extract_automata_size.py evaluation_results/ann:y_heuristic:y_fst:y/evaluation_results.json evaluation_results/ann:y_heuristic:y_fst:y/automata_sizes.csv

python3 src/stream/scripts/plots.py evaluation_results/overview_heuristic:y_fst:y.csv evaluation_results/bug_detection_heuristic:y_fst:y.csv evaluation_results/ann:y_heuristic:y_fst:y/length_time_pairs.csv evaluation_results/ann:y_heuristic:y_fst:y/automata_sizes.csv --output_dir evaluation_results/plots/

