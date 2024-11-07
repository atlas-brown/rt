#!/bin/sh

. getlogs.sh

cwd=`pwd`

rm -rf logs
mkdir logs
cp logs.tar.gz logs
cd logs
tar xvf logs.tar.gz
rm -rf logs.tar.gz

rm -rf big.log
for i in `ls *.log`
do
    cat $i >> big.log
done

rm -rf $cwd/numbers.txt
for i in {0..9}
do
    res=`cat big.log|grep "\[$i\]"|wc -l`
    echo "Count $i: $res" >> $cwd/numbers.txt
done
rm -rf big.log

cd $cwd
rm -rf logs
