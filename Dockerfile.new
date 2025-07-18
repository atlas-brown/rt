# https://hub.docker.com/_/python#simple-tags
FROM python:3.12.11-slim-bookworm

# https://hub.docker.com/_/eclipse-temurin#using-a-different-base-image
ENV JAVA_HOME="/opt/java/openjdk"
COPY --from=eclipse-temurin:21 $JAVA_HOME $JAVA_HOME
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# https://github.com/binpash/libdash?tab=readme-ov-file#what-are-the-dependencies
RUN apt-get update && \
    apt-get install --yes \
        autoconf \
        libtool \
        make && \
    apt-get clean

# rt dependencies
RUN pip install --no-cache-dir \
    jpype1 \
    libdash \
    pash_annotations \
    pytest \
    pyyaml \
    shasta

# create non-root user and copy local files to home directory
RUN useradd --create-home --shell /bin/bash rt
WORKDIR /home/rt
ADD ./ ./

# set PYTHONPATH and run debug
ENV PYTHONPATH="src"
CMD [ "python", "-m", "stream.run_evaluations" ]

# ideally, at some point, the entrypoint will a "main" executable,
# the user will specify commands through the command line (docker run rt run-benchmark --bare),
# and a CMD directive will have the "default" set of commands
# as CMD directives are made to be easily overriden
#ENTRYPOINT [ "python", "-m", "main" ]
#CMD [ "run-benchmark", "--bare" ]
