FROM python:3.12.11-slim-bookworm

# https://hub.docker.com/_/eclipse-temurin#using-a-different-base-image
ENV JAVA_HOME="/opt/java/openjdk"
COPY --from=eclipse-temurin:21 $JAVA_HOME $JAVA_HOME
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Set up PYTHONPATH
ENV PYTHONPATH="/home/StreamTypes/src"

# Install base dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    git \
    curl \
    build-essential \
    pkg-config \
    libssl-dev \
    ca-certificates \
    autoconf \
    libtool \
    make \
    && rm -rf /var/lib/apt/lists/*

# # Install Rust toolchain for stream-monitor
# RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
# RUN /root/.cargo/bin/cargo install rust-script

# # Add Cargo binaries to PATH
# ENV PATH="/root/.cargo/bin:$PATH"

# Install python dependencies (includes dependencies for stream types)
RUN pip install --no-cache-dir \
    jpype1 \
    libdash \
    pash_annotations \
    pytest \
    pyyaml \
    shasta \
    click \
    python-dotenv

# Create working directory
WORKDIR /home/StreamTypes

# Copy the entire project (including submodules)
COPY . /home/StreamTypes

# Default to bash
CMD [ "/bin/bash" ]
