#!/bin/sh
while getopts "vr" f
do
  case "$f" in
    v) echo "verbose" ;;
    r) echo "recursive" ;;
  esac
done