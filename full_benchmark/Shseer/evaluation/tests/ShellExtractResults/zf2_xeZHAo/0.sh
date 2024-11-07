#!/usr/bin/env bash

#
# runs test
# @author Anton Zagorskiy amberovsky@gmail.com
#
# usage: ./bin/test.sh
#

set -e
./vendor/bin/phpunit --configuration ./test/phpunit.xml
