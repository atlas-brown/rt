#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo "[1/4] Running the unit test suite"
bash ./run_tests.sh -q


echo "[2/4] Checking a known-invalid pipeline"
bash ./typecheck.sh -f evaluation_pipelines/invalid/3.sh

if [[ "${RT_SKIP_ANNOTATION_CHECK:-0}" != "1" ]]; then
  echo "[3/4] Checking the annotation-focused example"
  bash ./typecheck.sh -f dummy_example.sh
else
  echo "[3/4] Skipping the annotation-focused example because RT_SKIP_ANNOTATION_CHECK=1"
fi

echo "[4/4] Checking a known-valid pipeline"
bash ./typecheck.sh -f evaluation_pipelines/valid/3.sh

echo
echo "Functionality check completed successfully."
