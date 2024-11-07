#!/bin/sh

pass() {
    echo "Pass: " $*
}

fail() {
    echo "FAIL: " $*
}

for test in tests/*
do
    $test
    if [ $? -eq 0 ]
    then
        pass $test
    else
        fail $test
    fi
done
