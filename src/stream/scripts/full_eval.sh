#!/bin/bash

set -euo pipefail

if [ ! -d ./.git ] || [ ! -d ./evaluation_results ]; then
    echo Error: this script is meant to be run from the repo root
    exit 1
fi

FORCE="${1:-}"

export PYTHONPATH=src
# Keep LadderTypes on the artifact type database for all baseline stages,
# including direct invocations of this lower-level script.
TYPEDB="$(pwd)/ltsh_config/typedb"
export TYPEDB

LOG_DIR="evaluation_results/reproduce_logs"
rm -rf "$LOG_DIR"
mkdir -p "$LOG_DIR"

TOTAL_STAGES=21
STAGE_INDEX=0

slugify() {
    printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/_/g; s/^_//; s/_$//'
}

stage_bar() {
    local done="$1"
    local width=24
    local filled=$((done * width / TOTAL_STAGES))
    local empty=$((width - filled))
    printf '['
    printf '%*s' "$filled" '' | tr ' ' '#'
    printf '%*s' "$empty" '' | tr ' ' '-'
    printf ']'
}

start_stage() {
    local label="$1"
    local log_file="$2"
    STAGE_INDEX=$((STAGE_INDEX + 1))
    printf '\n%s %02d/%02d %s\n' "$(stage_bar "$STAGE_INDEX")" "$STAGE_INDEX" "$TOTAL_STAGES" "$label"
}

log_command() {
    printf 'Command:'
    printf ' %q' "$@"
    printf '\n\n'
}

append_command() {
    local log_file="$1"
    shift
    log_command "$@" >> "$log_file"
}

run_logged() {
    local label="$1"
    shift
    local log_file
    log_file="$LOG_DIR/$(slugify "$label").log"
    start_stage "$label" "$log_file"
    {
        log_command "$@"
        "$@"
    } > "$log_file" 2>&1 || {
        local status=$?
        printf '  failed with exit code %s\n' "$status"
        exit "$status"
    }
    printf '  done\n'
}

run_rt() {
    local label="$1"
    local outdir="$2"
    shift 2
    local log_file
    log_file="$LOG_DIR/$(slugify "$label").log"
    start_stage "$label" "$log_file"
    if [ ! -f "$outdir/evaluation_results.json" ] || [ -n "$FORCE" ]; then
        : > "$log_file"
        append_command "$log_file" python3 src/stream/run_evaluations.py "$@" --outdir "$outdir" --progress --progress-label "$label" --log-file "$log_file"
        python3 src/stream/run_evaluations.py "$@" --outdir "$outdir" --progress --progress-label "$label" --log-file "$log_file" || {
            local status=$?
            printf '  failed with exit code %s\n' "$status"
            exit "$status"
        }
        printf '  done\n'
    else
        printf 'cached\n' > "$log_file"
        printf '  cached\n'
    fi
}

run_baseline() {
    local label="$1"
    local log_file
    log_file="$LOG_DIR/$(slugify "$label").log"
    start_stage "$label" "$log_file"
    if [ ! -f evaluation_results/baseline.csv ] || [ -n "$FORCE" ]; then
        : > "$log_file"
        append_command "$log_file" python3 src/stream/scripts/baseline.py --progress --progress-label "$label" --log-file "$log_file"
        python3 src/stream/scripts/baseline.py --progress --progress-label "$label" --log-file "$log_file" || {
            local status=$?
            printf '  failed with exit code %s\n' "$status"
            exit "$status"
        }
        printf '  done\n'
    else
        printf 'cached baseline.csv\n' > "$log_file"
        printf '  skipped: cached baseline.csv\n'
    fi
}

run_summary() {
    local label="$1"
    local category_output="$2"
    shift 2
    local log_file
    log_file="$LOG_DIR/$(slugify "$label").log"
    start_stage "$label" "$log_file"
    {
        log_command python3 src/stream/evaluation_summary.py "$@" ">" "$category_output"
        python3 src/stream/evaluation_summary.py "$@" > "$category_output"
    } > "$log_file" 2>&1 || {
        local status=$?
        printf '  failed with exit code %s\n' "$status"
        exit "$status"
    }
    printf '  done\n'
}

skip_stage() {
    local label="$1"
    local reason="$2"
    local log_file
    log_file="$LOG_DIR/$(slugify "$label").log"
    start_stage "$label" "$log_file"
    printf '%s\n' "$reason" > "$log_file"
    printf '  skipped: %s\n' "$reason"
}

if [ -n "$FORCE" ]; then
    rm -rf \
        evaluation_results/ann:y_heuristic:y_fst:y \
        evaluation_results/ann:n_heuristic:y_fst:y \
        evaluation_results/ann:y_heuristic:n_fst:y \
        evaluation_results/ann:n_heuristic:n_fst:y \
        evaluation_results/ann:y_heuristic:y_fst:n \
        evaluation_results/ann:n_heuristic:y_fst:n \
        evaluation_results/ann:y_heuristic:n_fst:n \
        evaluation_results/ann:n_heuristic:n_fst:n \
        evaluation_results/ann:y_heuristic:y_fst:y_concretization:n \
        evaluation_results/ann:n_heuristic:y_fst:y_concretization:n
    rm -f \
        evaluation_results/ablation_table.md \
        evaluation_results/timing_table.md \
        evaluation_results/baseline.csv \
        evaluation_results/baseline.json \
        evaluation_results/merged_results_heuristic:*.csv \
        evaluation_results/bug_detection_heuristic:*.csv \
        evaluation_results/bug_detection_categories_heuristic:*.txt \
        evaluation_results/overview_heuristic:*.csv \
        evaluation_results/analysis_time_stats_fst:*.csv \
        evaluation_results/plots/*.pdf
fi

# `no_ignored_input` is a core compatibility check: piping non-empty input into
# a command that does not consume stdin is a direct stream contract violation,
# not a heuristic. Keep it enabled in the "heuristic:n" ablation.
DISABLE_HEURISTICS_FLAGS=(
    --disable_rule_no_empty_output
    --disable_rule_no_meaningless_command
    --disable_rule_no_sort_non_numeric_with_numeric_input
)

run_baseline "ShellCheck/LadderTypes baseline"

run_rt "RT w/ ann, w/ heuristics, w/ FSTs, w/ concretization" \
    evaluation_results/ann:y_heuristic:y_fst:y
run_rt "RT w/o ann, w/ heuristics, w/ FSTs, w/ concretization" \
    evaluation_results/ann:n_heuristic:y_fst:y \
    --disable_annotation
run_rt "RT w/ ann, w/o heuristics, w/ FSTs, w/ concretization" \
    evaluation_results/ann:y_heuristic:n_fst:y \
    "${DISABLE_HEURISTICS_FLAGS[@]}"
run_rt "RT w/o ann, w/o heuristics, w/ FSTs, w/ concretization" \
    evaluation_results/ann:n_heuristic:n_fst:y \
    "${DISABLE_HEURISTICS_FLAGS[@]}" --disable_annotation
run_rt "RT w/ ann, w/ heuristics, w/o FSTs, w/ concretization" \
    evaluation_results/ann:y_heuristic:y_fst:n \
    --disable_fsts
run_rt "RT w/ ann, w/ heuristics, w/ FSTs, w/o concretization" \
    evaluation_results/ann:y_heuristic:y_fst:y_concretization:n \
    --disable_concretization
run_rt "RT w/o ann, w/ heuristics, w/ FSTs, w/o concretization" \
    evaluation_results/ann:n_heuristic:y_fst:y_concretization:n \
    --disable_annotation --disable_concretization
run_rt "RT w/ ann, w/o heuristics, w/o FSTs, w/ concretization" \
    evaluation_results/ann:y_heuristic:n_fst:n \
    "${DISABLE_HEURISTICS_FLAGS[@]}" --disable_fsts
run_rt "RT w/o ann, w/ heuristics, w/o FSTs, w/ concretization" \
    evaluation_results/ann:n_heuristic:y_fst:n \
    --disable_annotation --disable_fsts
run_rt "RT w/o ann, w/o heuristics, w/o FSTs, w/ concretization" \
    evaluation_results/ann:n_heuristic:n_fst:n \
    "${DISABLE_HEURISTICS_FLAGS[@]}" --disable_annotation --disable_fsts

for f in y n; do
    for h in y n; do
        label="summary heuristic:$h fst:$f"
        ann_dir="evaluation_results/ann:y_heuristic:${h}_fst:${f}"
        raw_dir="evaluation_results/ann:n_heuristic:${h}_fst:${f}"
        category_output="evaluation_results/bug_detection_categories_heuristic:${h}_fst:${f}.txt"
        if [ -f "$ann_dir/evaluation_results.json" ] && [ -f "$raw_dir/evaluation_results.json" ]; then
            run_summary "$label" "$category_output" \
                --ann_csv "$ann_dir/results.csv" \
                --ann_json "$ann_dir/evaluation_results.json" \
                --raw_csv "$raw_dir/results.csv" \
                --raw_json "$raw_dir/evaluation_results.json" \
                --baseline_csv evaluation_results/baseline.csv \
                --merged_csv "evaluation_results/merged_results_heuristic:${h}_fst:${f}.csv" \
                --bug_detection_csv "evaluation_results/bug_detection_heuristic:${h}_fst:${f}.csv" \
                --overview_csv "evaluation_results/overview_heuristic:${h}_fst:${f}.csv"
        else
            skip_stage "$label" "missing annotated or raw evaluation output"
        fi
    done
done

run_logged "performance with FSTs" \
    python3 src/stream/scripts/performance.py \
    evaluation_results/ann:y_heuristic:y_fst:y/evaluation_results.json \
    evaluation_results/baseline.csv \
    evaluation_results/ann:y_heuristic:y_fst:y/length_time_pairs.csv \
    evaluation_results/analysis_time_stats_fst:y.csv
run_logged "performance without FSTs" \
    python3 src/stream/scripts/performance.py \
    evaluation_results/ann:y_heuristic:y_fst:n/evaluation_results.json \
    evaluation_results/baseline.csv \
    evaluation_results/ann:y_heuristic:y_fst:n/length_time_pairs.csv \
    evaluation_results/analysis_time_stats_fst:n.csv
run_logged "automata sizes" \
    python3 src/stream/scripts/extract_automata_size.py \
    evaluation_results/ann:y_heuristic:y_fst:y/evaluation_results.json \
    evaluation_results/ann:y_heuristic:y_fst:y/automata_sizes.csv

run_logged "ablation table" python3 src/stream/scripts/ablation_table.py
run_logged "timing table" python3 src/stream/scripts/timing_table.py
run_logged "plots" \
    python3 src/stream/scripts/plots.py \
    evaluation_results/overview_heuristic:y_fst:y.csv \
    evaluation_results/bug_detection_heuristic:y_fst:y.csv \
    evaluation_results/ann:y_heuristic:y_fst:y/automata_sizes.csv \
    --output_dir evaluation_results/plots/
