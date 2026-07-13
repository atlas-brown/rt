#! /usr/bin/env sh

set -eu

if ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker is not installed" >&2
    echo "  Install it from https://docs.docker.com/get-docker/" >&2
    exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
    echo "Error: curl is not installed" >&2
    exit 1
fi

repo="atlas-brown/rt"
branch="${RT_BRANCH:-main}"
bin_name="rt"
install_dir="${HOME}/.local/bin"
target="${install_dir}/${bin_name}"

mkdir -p "${install_dir}"

printf "%s" "Downloading rt..."

curl -fsSL "https://raw.githubusercontent.com/${repo}/${branch}/scripts/run-in-container.sh" -o "${target}"
chmod +x "${target}"

echo " done"

printf "%s" "Pulling Docker image..."
docker pull "ghcr.io/${repo}:latest" >/dev/null 2>&1 || {
    echo " failed"
    echo "" >&2
    echo "Error: could not pull ghcr.io/${repo}:latest" >&2
    echo "" >&2
    echo "  See https://github.com/${repo}#installation for manual installation." >&2
    echo "" >&2
    rm -f "${target}"
    exit 1
}
echo " done"

echo ""
echo "Rt installed to ${target}"

case ":${PATH}:" in
    *":${install_dir}:"*) ;;
    *)
        echo "Add ~/.local/bin to your PATH:"
        echo "  export PATH=\$HOME/.local/bin:\$PATH"
        ;;
esac

echo ""
echo "Try it:"
echo "  rt --help"
