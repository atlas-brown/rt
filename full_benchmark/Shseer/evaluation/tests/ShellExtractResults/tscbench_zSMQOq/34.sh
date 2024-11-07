#!/bin/sh

curdir=`pwd`
cd ../../../

echo "#" `date`
for i in `seq 1 100`; do
    echo -n "$i"
    ./run-benchmark.sh 2>&1 | grep overhead | cut -d':' -f2
done

cd $curdir
