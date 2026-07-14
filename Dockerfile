# Target 1: Containerized development of the system
FROM python:3.12-slim-trixie AS dev

# Copy the uv binaries from the official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# https://hub.docker.com/_/eclipse-temurin#using-a-different-base-image
ENV JAVA_HOME=/opt/java/openjdk
COPY --from=eclipse-temurin:21 $JAVA_HOME $JAVA_HOME
ENV PATH=${JAVA_HOME}/bin:${PATH}

# See https://github.com/binpash/libdash?tab=readme-ov-file#what-are-the-dependencies
# Certificates are needed for uv to be able to clone libdash over HTTPS
RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
        git \
        autoconf \
        automake \
        libtool \
        make \
        ca-certificates && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Change working directory
WORKDIR /app

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
CMD ["/usr/bin/env", "bash"]

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
RUN chown -R nonroot:nonroot /app
USER nonroot

# Entry for system usage
ENTRYPOINT ["/app/.venv/bin/rt"]
