#!/bin/sh

cat data.txt |awk '{print $1}' > ips.txt

# for all ips in ips.txt file
count=1
for myip in `cat ips.txt`
do

command="cd ~/AT/AugmentedTimePython/Socket/;git reset --hard;git pull;rm events.log nohup.out"

cert=`cat data.txt |grep "$myip "|awk '{print $2}'`
scp -i cert/$cert ubuntu@$myip:/home/ubuntu/AT/AugmentedTimePython/Socket/events.log $myip.events.log
scp -i cert/$cert ubuntu@$myip:/home/ubuntu/AT/AugmentedTimePython/Socket/nohup.out $myip.nohup.out

count=$((count + 1))
done

rm ips.txt

rm -rf logs.tar.gz
tar cvfz logs.tar.gz `ls *.log` `ls *.out`
rm -rf *.log *.out
