#!/bin/sh

dir=$1
file_count=$(find $dir -type f | wc -l)
echo "Total number of files: $file_count"
