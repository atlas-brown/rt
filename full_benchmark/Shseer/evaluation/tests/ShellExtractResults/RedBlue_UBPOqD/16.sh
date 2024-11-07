#!/bin/sh
DIR=""
if [ -z $1 ];
	then
	DIR=`pwd`
else
	DIR=$1
fi
for i in Shopping Browsing Ordering; do
	for j in Mysql TxMudAllBlue TxMudRedBlue ; do
		tail  -q -n1 ${DIR}/${i}_${j}_*gnuplot | sort > ${DIR}/${i}_${j}.data
	done;

done;
