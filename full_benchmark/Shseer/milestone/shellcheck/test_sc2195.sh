#!/bin/sh
set -- 
case "$1" in     # No trailing space
  value) echo "Match" # never matched because $1 is unset
esac