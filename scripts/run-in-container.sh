#! /usr/bin/env bash

set -euo pipefail

image="${RT_IMAGE:-ghcr.io/atlas-brown/rt:latest}"
runtime="${RT_RUNTIME:-docker}"

if ! command -v "$runtime" &>/dev/null; then
    echo "rt: '$runtime' not found" >&2
    echo "    install Docker from https://docs.docker.com/get-docker/" >&2
    exit 1
fi

if ! "$runtime" image inspect "$image" &>/dev/null; then
    echo "rt: pulling '$image'..." >&2
    "$runtime" pull "$image" >&2 || {
        echo "rt: failed to pull '$image'" >&2
        echo "    build locally:  docker build --target sys -t rt . " >&2
        echo "    then set:       export RT_IMAGE=rt" >&2
        exit 1
    }
fi

rt_args=()
runtime_args=()

if [ -t 0 ]; then
    runtime_args+=("--tty")
fi

for arg; do
    if [ -f "$arg" ]; then
        arg_abs="$(realpath "$arg")"
        rt_args+=("$arg_abs")
        runtime_args+=(-v "${arg_abs}:${arg_abs}:ro")
    else
        rt_args+=("$arg")
    fi
done

exec "$runtime" run --rm --interactive "${runtime_args[@]}" "$image" "${rt_args[@]}"
