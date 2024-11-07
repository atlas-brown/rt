#!/usr/bin/env bash

set -e

clean_up () {
    ARG=$?
    docker-compose down --volumes
    exit $ARG
}
trap clean_up EXIT

docker-compose up -d --renew-anon-volumes

export SPRING_PROFILES_ACTIVE=h2
echo "Testing with $SPRING_PROFILES_ACTIVE profile"
${PWD%/*samples/*}/scripts/compileWithMaven.sh $* &&  ${PWD%/*samples/*}/scripts/test.sh $*

echo "Testing with $SPRING_PROFILES_ACTIVE profile"
export SPRING_PROFILES_ACTIVE=postgresql
${PWD%/*samples/*}/scripts/compileWithMaven.sh $* &&  ${PWD%/*samples/*}/scripts/test.sh $*
