#! /usr/bin/env sh

set -eu

root="$(cd "$(dirname "$0")/.." && pwd)"
version="${1:-${VERSION:-0.1.0}}"
out="${root}/dist"

if ! command -v nfpm >/dev/null 2>&1; then
    echo "Error: nfpm is not installed" >&2
    exit 1
fi

mkdir -p "${out}"
rm -f "${out}"/rt-*.rpm

VERSION="${version}" nfpm package -f "${root}/packaging/nfpm.yaml" -p rpm -t "${out}/"

rpm=$(ls "${out}"/rt-*.rpm)
echo "created ${rpm}"
if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${rpm}"
else
    shasum -a 256 "${rpm}"
fi
