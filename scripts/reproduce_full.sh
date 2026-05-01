#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
cat <<'EOF'
This script runs the full reproduction pipeline for the artifact.

Expected external prerequisites for the full pipeline:
- Python 3
- Java runtime
- shellcheck
- upstream ltsh installed from https://github.com/michaelsippel/ltsh
- Python packages from requirements.txt
  (including pandas, numpy, matplotlib, matplotlib-set-diagrams, and tqdm)

It will:
1. Generate baseline data
2. Run the main evaluation and ablations
3. Merge the outputs
4. Regenerate the summary plots

Primary generated outputs include:
- evaluation_results/tables/ablation_table.md
- evaluation_results/tables/timing_table.md
- evaluation_results/plots/accuracy-chart-with-annotations.pdf
- evaluation_results/plots/accuracy-chart-without-annotations.pdf
- evaluation_results/plots/bug-detection.pdf
- evaluation_results/plots/automata-sizes.pdf

The bug-detection plot compares the unannotated RT run against ShellCheck and
LadderTypes, with the RT system labeled simply as RT.
EOF
  exit 0
fi

# Use the repository-local LadderTypes database. For the fair comparison, this database preserves the original upstream entries and adds RT simple types on top.
export TYPEDB="$repo_root/ltsh_config/typedb"

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
