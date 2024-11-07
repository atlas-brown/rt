#!/bin/sh

ps cax | grep docker > /dev/null
if [ $? -eq 1 ]; then
    # start docker
    dockerd -H unix:///var/run/docker.sock &> /var/log/docker.log &
fi

docker $@

