#!/bin/sh

rm -rf build
if [ -d build ]; 
then
    # unreachable as the build directory does not exist
    echo "Contents of build dir"
    ls build
fi