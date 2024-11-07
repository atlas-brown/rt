#! /bin/sh

# Bind benchmark to cpu and memory node
LASTCPU=`cat /proc/cpuinfo | grep processor | tail -n1 | cut -d':' -f2`

#taskset 2 ./tscbench
numactl --physcpubind="$LASTCPU" --localalloc ./tscbench
