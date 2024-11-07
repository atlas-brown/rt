#!/bin/sh

PRINCIPAL=${PRINCIPAL:-root}

if [ -n "$SECRET" ]; then
    export MARATHON_MESOS_AUTHENTICATION_PRINCIPAL=${MARATHON_MESOS_AUTHENTICATION_PRINCIPAL:-$PRINCIPAL}
    touch /tmp/secret
    chmod 600 /tmp/secret
    printf '%s' "$SECRET" > /tmp/secret
    export MARATHON_MESOS_AUTHENTICATION_SECRET_FILE=/tmp/secret
fi

exec "$@"
