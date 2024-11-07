#!/bin/bash
export CONNECT_PASSWORD=""
exec ssh -o ProxyCommand="nc -X 4 -x localhost:9050 %h %p" $*