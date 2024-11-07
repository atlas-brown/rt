#!/bin/sh

#if [ $# -ne 1 ]; then
#    echo "Usage: $0 target_url" 1>&2
#    exit 1
#fi

exec java -classpath "./conf:./lib/*" net.pupha.wsc.WSC $*

