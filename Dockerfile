# Use the official Ubuntu base image
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Update and install basic packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    software-properties-common \
    unzip \
    vim \
    sudo \ 
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Add deadsnakes PPA and install Python 3.10
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.10 python3.10-venv && \
    rm -rf /var/lib/apt/lists/*

# Set Python 3.10 as the default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Install pip for Python 3.10
RUN python3 -m ensurepip --upgrade

# Verify Python and pip versions
RUN python3 --version && pip3 --version


#COPY z3 install script
# COPY install_z3.sh /home/stream/install_z3.sh
# RUN chmod +x /home/stream/install_z3.sh
# RUN /home/stream/install_z3.sh

# Install Python dependencies
# RUN sudo apt-get install libtool m4 automake -y

RUN pip3 install --no-cache-dir shasta libdash pash_annotations pytest z3-solver

# Set the working directory in the container
WORKDIR /home/stream

ADD . /home/stream
# RUN bash /home/stream/run_tests.sh

# The command the container will run by default
SHELL ["/bin/bash", "-c"]

CMD ["/bin/bash"]

