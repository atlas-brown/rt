#! /usr/bin/env sh
set -eu

root="$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)"
version="${1:-${VERSION:-0.1.0}}"
out="${root}/dist"
stage="${out}/stage/rt-${version}"
tarball="${out}/rt-${version}.tar.gz"

rm -rf "${out}/stage"
mkdir -p "${stage}/scripts"
cp "${root}/scripts/run-in-container.sh" "${stage}/scripts/"

rm -f "${tarball}"
if tar --version 2>&1 | grep -q 'GNU tar'; then
	tar -C "${out}/stage" \
		--sort=name \
		--mtime='UTC 1970-01-01' \
		--owner=0 --group=0 --numeric-owner \
		-czf "${tarball}" "rt-${version}"
else
	COPYFILE_DISABLE=1 tar -C "${out}/stage" -czf "${tarball}" "rt-${version}"
fi

echo "created ${tarball}"
if command -v sha256sum >/dev/null 2>&1; then
	sha256sum "${tarball}"
else
	shasum -a 256 "${tarball}"
fi
