#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo "Running the unit test suite"
PYTHONPATH=src python3 -m pytest --ignore=./full_benchmark -q

echo "Running smoke tests: bash rt.sh examples/motivating_example.sh"
set +e
bash rt.sh examples/motivating_example.sh
smoke_status=$?
set -e

if [[ "$smoke_status" -eq 0 ]]; then
  echo "Expected the motivating-example smoke test to report an RT error." >&2
  exit 1
fi

if [[ "$smoke_status" -ne 1 ]]; then
  exit "$smoke_status"
fi
