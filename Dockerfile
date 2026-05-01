FROM python:3.12.11-slim-bookworm

ARG LTSH_COMMIT=1ab8db590b41ed86a2307258ccbb62a6652a4ae7
ARG LADDER_TYPES_COMMIT=3b85bd76217d4d4199bc5f305f80ac3d2b9e20a6

# https://hub.docker.com/_/eclipse-temurin#using-a-different-base-image
ENV JAVA_HOME="/opt/java/openjdk"
COPY --from=eclipse-temurin:21 $JAVA_HOME $JAVA_HOME
ENV PATH="${JAVA_HOME}/bin:${PATH}"
ENV LTSH_REPO_DIR="/opt/ltsh"
ENV TYPEDB="/home/StreamTypes/ltsh_config/typedb"

# Set up PYTHONPATH
ENV PYTHONPATH="/home/StreamTypes/src"

# Install base dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    git \
    curl \
    build-essential \
    cargo \
    rustc \
    pkg-config \
    libssl-dev \
    ca-certificates \
    autoconf \
    libtool \
    make \
    shellcheck \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /home/StreamTypes

# Copy the entire project (including submodules)
COPY . /home/StreamTypes

RUN git init -q

# Install python dependencies, including plotting packages for the full pipeline
RUN pip install --no-cache-dir -r requirements.txt

# Install upstream ltsh and replace its typedb with the repository's fairness-adjusted copy
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
    cp /home/StreamTypes/ltsh_config/typedb "${LTSH_REPO_DIR}/typedb"; \
    cargo install --root /usr/local --path "${LTSH_REPO_DIR}"

# Default to bash
CMD [ "/bin/bash" ]
