#!/bin/bash
rm big.log
cat *.log > big.log
count=0
sum=0
while read name
do
   lc=`echo $name|cut -d":" -f3`
   ph=`echo $name|cut -d":" -f5`
   diff=$((lc-ph))
    if [ $diff -ne 0 ]
    then
        count=$((count+1))
        sum=$((sum+diff))
    fi
done < big.log
avg=$((sum/count))
echo $avg > avg
        
