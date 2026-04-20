FROM python:3.12.11-slim-bookworm

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

# Install python dependencies, including plotting packages for the full pipeline
RUN pip install --no-cache-dir -r requirements.txt

# Install upstream ltsh and replace its typedb with the repository's fairness-adjusted copy
RUN git clone --depth 1 --branch dev https://github.com/michaelsippel/ltsh "${LTSH_REPO_DIR}" \
    && cp /home/StreamTypes/ltsh_config/typedb "${LTSH_REPO_DIR}/typedb" \
    && cargo install --root /usr/local --path "${LTSH_REPO_DIR}"

# Default to bash
CMD [ "/bin/bash" ]
