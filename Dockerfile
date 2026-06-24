# Target 1: Containerized development of the system
FROM python:3.12-slim-trixie AS dev

ARG LTSH_COMMIT=1ab8db590b41ed86a2307258ccbb62a6652a4ae7
ARG LADDER_TYPES_COMMIT=3b85bd76217d4d4199bc5f305f80ac3d2b9e20a6

# https://hub.docker.com/_/eclipse-temurin#using-a-different-base-image
ENV JAVA_HOME="/opt/java/openjdk"
COPY --from=eclipse-temurin:21 $JAVA_HOME $JAVA_HOME
ENV PATH="${JAVA_HOME}/bin:${PATH}"
ENV LTSH_REPO_DIR="/opt/ltsh"
ENV TYPEDB="/home/StreamTypes/ltsh_config/typedb"
ENV PYTHONPATH="/home/StreamTypes/src"

# Copy the uv binaries from the official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# See https://github.com/binpash/libdash?tab=readme-ov-file#what-are-the-dependencies
# Certificates are needed for uv to be able to clone libdash over HTTPS
RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
        git \
        curl \
        build-essential \
        cargo \
        rustc \
        pkg-config \
        libssl-dev \
        autoconf \
        automake \
        libtool \
        make \
        shellcheck \
        ca-certificates && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY ltsh_config/typedb /tmp/stream-typedb

# Install the same upstream ltsh baseline used by the AE artifact.
RUN set -eux; \
    git clone https://github.com/michaelsippel/ltsh "${LTSH_REPO_DIR}"; \
    git -C "${LTSH_REPO_DIR}" checkout --detach "${LTSH_COMMIT}"; \
    git clone https://github.com/michaelsippel/lib-laddertypes.git /opt/lib-laddertypes; \
    git -C /opt/lib-laddertypes checkout --detach "${LADDER_TYPES_COMMIT}"; \
    mkdir -p /opt/lib-tinydiagnostics/src; \
    printf '%s\n' \
      '[package]' \
      'name = "tiny-diagnostics"' \
      'version = "0.1.0"' \
      'edition = "2018"' \
      '' \
      '[lib]' \
      'name = "tiny_diagnostics"' \
      'path = "src/lib.rs"' \
      > /opt/lib-tinydiagnostics/Cargo.toml; \
    printf '%s\n' \
      '#[derive(Copy, Clone, Debug, Default, PartialEq, Eq, Hash)]' \
      'pub struct InputRegionTag {' \
      '    pub begin: usize,' \
      '    pub end: usize,' \
      '}' \
      '' \
      'impl InputRegionTag {' \
      '    pub fn max(a: Self, b: Self) -> Self {' \
      '        Self {' \
      '            begin: a.begin.min(b.begin),' \
      '            end: a.end.max(b.end),' \
      '        }' \
      '    }' \
      '}' \
      '' \
      '#[derive(Clone, Debug, PartialEq, Eq, Hash)]' \
      'pub struct ParseInfo<T> {' \
      '    pub char_range: InputRegionTag,' \
      '    pub info: T,' \
      '}' \
      > /opt/lib-tinydiagnostics/src/lib.rs; \
    sed -i 's#laddertypes = .*#laddertypes = { path = "../lib-laddertypes" }#' "${LTSH_REPO_DIR}/Cargo.toml"; \
    cp /tmp/stream-typedb "${LTSH_REPO_DIR}/typedb"; \
    cargo install --root /usr/local --path "${LTSH_REPO_DIR}"

# Change working directory
WORKDIR /home/StreamTypes

# Copy from the cache instead of linking since it's a mounted volume
# See https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# Install dependencies
# See https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Easily overwritable entry for development
CMD ["/bin/bash"]

# ----------------------------------------

# Target 2: Containerized usage of the system
FROM dev AS sys

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot && \
    useradd --system --gid 999 --uid 999 --create-home nonroot

# Copy the necessary project files and install
COPY pyproject.toml uv.lock README.md ./
COPY jars ./jars
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Change into the non root user
RUN chown -R nonroot:nonroot /home/StreamTypes
USER nonroot

# Entry for system usage
ENTRYPOINT ["/home/StreamTypes/.venv/bin/rt"]
