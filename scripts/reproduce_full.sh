#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

cat <<'EOF'
This script runs the full reproduction pipeline for the artifact.

Expected external prerequisites for the full pipeline:
- Python 3
- Java runtime
- shellcheck
- ltsh
- pandas
- numpy
- matplotlib
- matplotlib-set-diagrams

It will:
1. Generate baseline data
2. Run the main evaluation and ablations
3. Merge the outputs
4. Regenerate the summary plots

Primary generated outputs include:
- evaluation_results/baseline.csv
- evaluation_results/baseline.json
- evaluation_results/merged_results_heuristic:y_fst:y.csv
- evaluation_results/bug_detection_heuristic:y_fst:y.csv
- evaluation_results/overview_heuristic:y_fst:y.csv
- evaluation_results/analysis_time_stats_fst:y.csv
- evaluation_results/plots/accuracy-chart.pdf
- evaluation_results/plots/bug-detection.pdf
- evaluation_results/plots/time-length-chart.pdf
- evaluation_results/plots/automata-sizes.pdf
EOF

if [[ "${1:-}" == "--force" ]]; then
  shift
  echo "Running full reproduction with forced regeneration."
  bash ./src/stream/scripts/full_eval.sh force "$@"
else
  echo "Running full reproduction using cached outputs when available."
  bash ./src/stream/scripts/full_eval.sh "$@"
fi

echo
echo "Full reproduction pipeline completed successfully."
