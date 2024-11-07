#!/bin/bash

 # change the setting : listener.http.internal = 127.0.0.1:_LISTENER_HTTP_INTERNAL_PORT_

sed -i 's/_LISTENER_HTTP_INTERNAL_PORT_/'"$PORT"'/' ~/.dpkg/etc/riak/riak.conf
