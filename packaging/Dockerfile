# Self-contained build environment for packaging/build.sh (.deb + .rpm).

FROM debian:trixie-slim

RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
        git curl ca-certificates \
        build-essential cargo rustc pkg-config libssl-dev \
        autoconf automake libtool make \
        ruby ruby-dev rpm && \
    gem install --no-document fpm && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /workspace
