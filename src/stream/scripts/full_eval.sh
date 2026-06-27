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

EVAL_ROOT=evaluation_results
BASELINE_DIR="$EVAL_ROOT/baseline"
DERIVED_DIR="$EVAL_ROOT/derived"
TABLES_DIR="$EVAL_ROOT/tables"
PLOTS_DIR="$EVAL_ROOT/plots"
BASELINE_CSV="$BASELINE_DIR/baseline.csv"
BASELINE_JSON="$BASELINE_DIR/baseline.json"
BASELINE_WARNINGS_JSON="$BASELINE_DIR/shellcheck_warnings.json"

mkdir -p "$BASELINE_DIR" "$DERIVED_DIR" "$TABLES_DIR" "$PLOTS_DIR"
rm -rf "$EVAL_ROOT/reproduce_logs" 2>/dev/null || true

clean_eval_root_files() {
    find "$EVAL_ROOT" -maxdepth 1 -type f -delete
}

clean_eval_root_files

TOTAL_STAGES=18
STAGE_INDEX=0

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
    STAGE_INDEX=$((STAGE_INDEX + 1))
    printf '\n%s %02d/%02d %s\n' "$(stage_bar "$STAGE_INDEX")" "$STAGE_INDEX" "$TOTAL_STAGES" "$label"
}

run_logged() {
    local label="$1"
    shift
    start_stage "$label"
    "$@" >/dev/null 2>&1 || {
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
    start_stage "$label"
    if [ ! -f "$outdir/evaluation_results.json" ] || [ -n "$FORCE" ]; then
        python3 src/stream/scripts/run_eval.py "$@" --outdir "$outdir" --progress --progress-label "$label" --log-file /dev/null || {
            local status=$?
            printf '  failed with exit code %s\n' "$status"
            exit "$status"
        }
        printf '  done\n'
    else
        printf '  cached\n'
    fi
}

run_baseline() {
    local label="$1"
    start_stage "$label"
    if [ ! -f "$BASELINE_CSV" ] || [ -n "$FORCE" ]; then
        python3 src/stream/scripts/baseline.py \
            --csv-file "$BASELINE_CSV" \
            --json-file "$BASELINE_JSON" \
            --warnings-json-file "$BASELINE_WARNINGS_JSON" \
            --progress --progress-label "$label" --log-file /dev/null || {
            local status=$?
            printf '  failed with exit code %s\n' "$status"
            exit "$status"
        }
        printf '  done\n'
    else
        printf '  skipped: cached %s\n' "$BASELINE_CSV"
    fi
}

run_summary() {
    local label="$1"
    local category_output="$2"
    shift 2
    start_stage "$label"
    python3 src/stream/scripts/summarize_eval.py "$@" > "$category_output" 2>/dev/null || {
        local status=$?
        printf '  failed with exit code %s\n' "$status"
        exit "$status"
    }
    printf '  done\n'
}

skip_stage() {
    local label="$1"
    local reason="$2"
    start_stage "$label"
    printf '  skipped: %s\n' "$reason"
}

if [ -n "$FORCE" ]; then
    rm -rf \
        "$BASELINE_DIR" \
        "$DERIVED_DIR" \
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
        "$TABLES_DIR"/ablation_table.md \
        "$TABLES_DIR"/timing_table.md \
        "$PLOTS_DIR"/*.pdf
    mkdir -p "$BASELINE_DIR" "$DERIVED_DIR" "$TABLES_DIR" "$PLOTS_DIR"
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
run_rt "RT w/o ann, w/ heuristics, w/o FSTs, w/ concretization" \
    evaluation_results/ann:n_heuristic:y_fst:n \
    --disable_annotation --disable_fsts

for summary_config in "y y" "n y" "y n"; do
    h="${summary_config%% *}"
    f="${summary_config##* }"
    label="summary heuristic:$h fst:$f"
    ann_dir="evaluation_results/ann:y_heuristic:${h}_fst:${f}"
    raw_dir="evaluation_results/ann:n_heuristic:${h}_fst:${f}"
    category_output="$DERIVED_DIR/bug_detection_categories_heuristic:${h}_fst:${f}.txt"
    if [ -f "$ann_dir/evaluation_results.json" ] && [ -f "$raw_dir/evaluation_results.json" ]; then
        run_summary "$label" "$category_output" \
            --ann_csv "$ann_dir/results.csv" \
            --ann_json "$ann_dir/evaluation_results.json" \
            --raw_csv "$raw_dir/results.csv" \
            --raw_json "$raw_dir/evaluation_results.json" \
            --baseline_csv "$BASELINE_CSV" \
            --merged_csv "$DERIVED_DIR/merged_results_heuristic:${h}_fst:${f}.csv" \
            --bug_detection_csv "$DERIVED_DIR/bug_detection_heuristic:${h}_fst:${f}.csv" \
            --overview_csv "$DERIVED_DIR/overview_heuristic:${h}_fst:${f}.csv"
    else
        skip_stage "$label" "missing annotated or raw evaluation output"
    fi
done

run_logged "performance with FSTs" \
    python3 src/stream/scripts/performance.py \
    evaluation_results/ann:y_heuristic:y_fst:y/evaluation_results.json \
    "$BASELINE_CSV" \
    evaluation_results/ann:y_heuristic:y_fst:y/length_time_pairs.csv \
    "$DERIVED_DIR/analysis_time_stats_fst:y.csv"
run_logged "performance without FSTs" \
    python3 src/stream/scripts/performance.py \
    evaluation_results/ann:y_heuristic:y_fst:n/evaluation_results.json \
    "$BASELINE_CSV" \
    evaluation_results/ann:y_heuristic:y_fst:n/length_time_pairs.csv \
    "$DERIVED_DIR/analysis_time_stats_fst:n.csv"
run_logged "automata sizes" \
    python3 src/stream/scripts/extract_automata_size.py \
    evaluation_results/ann:y_heuristic:y_fst:y/evaluation_results.json \
    evaluation_results/ann:y_heuristic:y_fst:y/automata_sizes.csv

run_logged "ablation table" python3 src/stream/scripts/ablation_table.py
run_logged "timing table" python3 src/stream/scripts/timing_table.py
run_logged "plots" \
    python3 src/stream/scripts/plots.py \
    "$DERIVED_DIR/overview_heuristic:y_fst:y.csv" \
    "$DERIVED_DIR/bug_detection_heuristic:y_fst:y.csv" \
    evaluation_results/ann:y_heuristic:y_fst:y/automata_sizes.csv \
    --output_dir "$PLOTS_DIR/"
clean_eval_root_files
