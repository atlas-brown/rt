#!/usr/bin/env bash
# Builds a .deb and a .rpm that install the `rt` / `rtr` CLIs system-wide,
# with no build tools required on the target machine.
#
# How it works, in short:
#   1. Copy the repo's pyproject.toml/uv.lock/src/jars into a scratch dir and
#      apply patches/001-portable-paths.patch
#   2. `uv sync --locked --no-dev` to resolve every dependency,
#      including the git-sourced libdash/shasta packages, which get compiled
#      from source using cargo/rustc *here*, at build time, so the target
#      machine never needs a Rust toolchain.
#   3. Physically copy the patched rt/ and rti/ packages on top of that
#      resolved site-packages directory, replacing uv's editable-install
#      pointer (a .pth file with a hardcoded absolute path) with real files.
#   4. Stage that site-packages dir + jars/ + a bundled Python runtime + two
#      tiny wrapper scripts into an fpm source tree and invoke fpm once per
#      target format (deb, rpm).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGING_DIR="$REPO_ROOT/packaging"
WORK_DIR="$PACKAGING_DIR/work"
OUT_DIR="$PACKAGING_DIR/dist"

PKG_NAME="rt-artifact"
PKG_VERSION="$(grep -m1 '^version' "$REPO_ROOT/pyproject.toml" | sed -E 's/.*"(.*)".*/\1/')"
PKG_ITERATION="1"
MAINTAINER="${RT_PACKAGE_MAINTAINER:-maintainer@email.com}"
DESCRIPTION="Rt: an overlay type system for shell pipelines -- static checker for shell pipelines (rt, rti)"
URL="https://github.com/atlas-brown/rt"
PY_VERSION="3.12"
PREFIX="/usr/lib/rt-artifact"

echo "==> Cleaning previous build state"
rm -rf "$WORK_DIR" "$OUT_DIR"
mkdir -p "$WORK_DIR" "$OUT_DIR"

echo "==> Staging a patched copy of the source tree"
SRC_WORK="$WORK_DIR/src-work"
mkdir -p "$SRC_WORK"
cp "$REPO_ROOT/pyproject.toml" "$REPO_ROOT/uv.lock" "$REPO_ROOT/README.md" "$SRC_WORK/"
cp -a "$REPO_ROOT/src" "$SRC_WORK/src"
cp -a "$REPO_ROOT/jars" "$SRC_WORK/jars"

git -C "$SRC_WORK" init -q
git -C "$SRC_WORK" add -A
git -C "$SRC_WORK" -c user.email=build@localhost -c user.name=build commit -q -m baseline
git -C "$SRC_WORK" apply --whitespace=nowarn "$PACKAGING_DIR/patches/001-portable-paths.patch"
echo "    patch applied cleanly"

echo "==> Fetching a relocatable, self-contained Python $PY_VERSION runtime via uv"
uv python install "$PY_VERSION" >/dev/null
MANAGED_PYTHON_DIR="$(dirname "$(dirname "$(readlink -f "$(uv python list --only-installed --managed-python | awk -v v="$PY_VERSION" '$0 ~ "cpython-"v"\\." {print $2; exit}')")")")"
if [[ ! -x "$MANAGED_PYTHON_DIR/bin/python$PY_VERSION" ]]; then
  echo "error: could not resolve a managed Python $PY_VERSION install (looked under $MANAGED_PYTHON_DIR)" >&2
  exit 1
fi
echo "    using $MANAGED_PYTHON_DIR"

echo "==> Resolving Python dependencies with uv (this builds libdash/shasta from source)"
( cd "$SRC_WORK" && uv sync --locked --no-dev --python "$MANAGED_PYTHON_DIR/bin/python$PY_VERSION" )

SITE_PACKAGES="$SRC_WORK/.venv/lib/python$PY_VERSION/site-packages"
if [[ ! -d "$SITE_PACKAGES" ]]; then
  echo "error: expected $SITE_PACKAGES to exist; is uv using a different Python version?" >&2
  exit 1
fi

echo "==> Replacing the editable-install pointer with relocatable package files"
rm -f "$SITE_PACKAGES"/_rt.pth "$SITE_PACKAGES"/rt.pth
rm -rf "$SITE_PACKAGES/rt" "$SITE_PACKAGES/rti"
cp -a "$SRC_WORK/src/rt" "$SITE_PACKAGES/rt"
cp -a "$SRC_WORK/src/rti" "$SITE_PACKAGES/rti"
find "$SITE_PACKAGES" -name "__pycache__" -type d -prune -exec rm -rf {} +
find "$SITE_PACKAGES/rt" "$SITE_PACKAGES/rti" -maxdepth 2 -iname "unit_tests" -type d -prune -exec rm -rf {} +

echo "==> Building the fpm source tree"
FPM_ROOT="$WORK_DIR/fpm-root"
mkdir -p "$FPM_ROOT$PREFIX/site-packages"
mkdir -p "$FPM_ROOT$PREFIX/jars"
mkdir -p "$FPM_ROOT/usr/bin"

cp -a "$SITE_PACKAGES"/. "$FPM_ROOT$PREFIX/site-packages/"
cp -a "$SRC_WORK/jars"/. "$FPM_ROOT$PREFIX/jars/"

# Only bin/ and lib/ are needed to run Python
mkdir -p "$FPM_ROOT$PREFIX/python"
cp -a "$MANAGED_PYTHON_DIR/bin" "$FPM_ROOT$PREFIX/python/bin"
cp -a "$MANAGED_PYTHON_DIR/lib" "$FPM_ROOT$PREFIX/python/lib"
find "$FPM_ROOT$PREFIX/python" -name "__pycache__" -type d -prune -exec rm -rf {} +

for cmd in rt rti; do
  entry_module="rt.main"
  [[ "$cmd" == "rti" ]] && entry_module="rti.main"
  cat > "$FPM_ROOT/usr/bin/$cmd" <<WRAPPER
#!/bin/sh
# Installed by the $PKG_NAME package. Runs the bundled Python interpreter
# against the dependency tree resolved at package-build time; see
# packaging/build.sh. Deliberately not the system python3, since the
# extensions in site-packages/ are tied to this exact interpreter's ABI.
export PYTHONPATH="$PREFIX/site-packages\${PYTHONPATH:+:\$PYTHONPATH}"
export RT_JARS_DIR="$PREFIX/jars"
exec "$PREFIX/python/bin/python$PY_VERSION" -m $entry_module "\$@"
WRAPPER
  chmod 755 "$FPM_ROOT/usr/bin/$cmd"
done

COMMON_FPM_ARGS=(
  --name "$PKG_NAME"
  --version "$PKG_VERSION"
  --iteration "$PKG_ITERATION"
  --maintainer "$MAINTAINER"
  --url "$URL"
  --description "$DESCRIPTION"
  --license "See upstream repository"
  --architecture native
  -s dir
  --chdir "$FPM_ROOT"
)

echo "==> Building .deb (Debian/Ubuntu)"
fpm "${COMMON_FPM_ARGS[@]}" \
  -t deb \
  --package "$OUT_DIR/" \
  --depends "shellcheck" \
  --depends "default-jre-headless | openjdk-21-jre-headless" \
  usr

echo "==> Building .rpm (Fedora/RHEL)"

fpm "${COMMON_FPM_ARGS[@]}" \
  -t rpm \
  --package "$OUT_DIR/" \
  --depends "ShellCheck" \
  --depends "java-headless" \
  --directories "$PREFIX" \
  usr

echo "==> Done. Packages in $OUT_DIR:"
ls -la "$OUT_DIR"
