#!/bin/sh
find -print0 | grep -z -P -e "(\.cpp|\.h)$" | xargs -0 cat | wc -l
