#!/bin/sh
total=`cat *.log|wc -l`
echo "$total"
for i in 0 1 2 3 4 5 6 7 8
do
    res=`cat *.log|grep "\[$i\]"|wc -l`
    pct=$((res*100000/total))
    echo "$i:$res:$pct"
done

