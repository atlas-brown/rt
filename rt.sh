#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}"

if [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then
  exec "$VIRTUAL_ENV/bin/python" -m stream.main "$@"
fi

if command -v uv >/dev/null 2>&1; then
  exec uv run python -m stream.main "$@"
fi

if [[ -x "$repo_root/.venv/bin/python" ]]; then
  exec "$repo_root/.venv/bin/python" -m stream.main "$@"
fi

exec python3 -m stream.main "$@"
