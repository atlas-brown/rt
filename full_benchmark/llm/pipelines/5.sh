#!/usr/bin/env bash
cat file.txt | sed 's/foo/bar/g' | grep "foo"
