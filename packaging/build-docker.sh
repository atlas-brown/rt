#!/usr/bin/env bash
# Runs packaging/build.sh (.deb + .rpm) inside a Docker container with every
# required build tool (uv, fpm, rpm, dpkg-deb, a Rust toolchain for the
# git-sourced libdash/shasta extensions)
#
# The repo is bind-mounted into the container, so packages land directly in
# packaging/dist/ on the host, same as running build.sh directly
#
# This is the same script .github/workflows/package.yml can run in CI
#
# NOTE: this covers Ubuntu (.deb) and Fedora (.rpm) only. The macOS/Homebrew
# side isn't a separate build script at all: packaging/homebrew/rt.rb builds
# from source directly against Homebrew's own python@3.12 when a user runs
# `brew install`, the same way any other source-built formula works
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_TAG="rt-packaging-builder:latest"

if ! command -v docker >/dev/null 2>&1; then
  echo "error: docker is required -- https://docs.docker.com/get-docker/" >&2
  exit 1
fi

echo "==> Building the packaging toolchain image ($IMAGE_TAG)"
docker build -t "$IMAGE_TAG" -f "$REPO_ROOT/packaging/Dockerfile" "$REPO_ROOT/packaging"

echo "==> Running packaging/build.sh inside the container"
docker run --rm \
  -v "$REPO_ROOT":/workspace \
  -w /workspace \
  "$IMAGE_TAG" \
  bash packaging/build.sh

echo "==> Done. Packages in packaging/dist/:"
ls -la "$REPO_ROOT/packaging/dist"
