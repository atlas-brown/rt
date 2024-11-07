#!/bin/sh

# step 1) compile the latest and greatest in disposal container
docker build -t tmetsch/mesos_docker_tmp -f Dockerfile.build .
docker create --name tmp_cont tmetsch/mesos_docker_tmp
docker cp tmp_cont:/tmp/mesos.tgz .
docker rm tmp_cont

# step 2) create actual container
docker build -t tmetsch/mesos_docker .

