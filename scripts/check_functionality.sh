#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

export PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}"

if [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then
  python_cmd=("$VIRTUAL_ENV/bin/python")
elif command -v uv >/dev/null 2>&1; then
  python_cmd=(uv run python)
elif [[ -x "$repo_root/.venv/bin/python" ]]; then
  python_cmd=("$repo_root/.venv/bin/python")
else
  python_cmd=(python3)
fi

echo "Running the unit test suite"
"${python_cmd[@]}" -m pytest --ignore=./full_benchmark -q

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
