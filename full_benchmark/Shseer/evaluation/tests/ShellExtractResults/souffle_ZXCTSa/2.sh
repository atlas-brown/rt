#!/bin/bash

### quickly show if cmake contains all the tests defined here.

dir=$1

tests=$(find $dir -maxdepth 1 -type d -printf "%f\n" | sort)
cmake_tests=$(sed 's/.*(\(.*\))/\1/' $dir/CMakeLists.txt | sort) 
comm -23 <(echo "$tests") <(echo "$cmake_tests")
