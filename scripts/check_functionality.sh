#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo "Running the unit test suite"
PYTHONPATH=src python3 -m pytest --ignore=./full_benchmark -q

echo "Running smoke tests: rt examples/motivating_example.sh"
set +e
PYTHONPATH=src python3 -m stream.main examples/motivating_example.sh
smoke_status=$?
set -e

if [[ "$smoke_status" -eq 0 ]]; then
  echo "Expected the motivating-example smoke test to report an RT error." >&2
  exit 1
fi

if [[ "$smoke_status" -ne 1 ]]; then
  exit "$smoke_status"
fi

echo "Running smoke tests: rtr check examples/motivating_example.sh"
set +e
PYTHONPATH=src python3 -m rtr.main check examples/motivating_example.sh
rtr_check_status=$?
set -e

if [[ "$rtr_check_status" -ne 1 ]]; then
  exit "$rtr_check_status"
fi

echo "Running smoke tests: rtr resolve grep"
PYTHONPATH=src python3 -m rtr.main resolve -i ".*" grep foo >/dev/null
