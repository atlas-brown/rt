#!/bin/sh

cat data.txt |awk '{print $1}' > ips.txt

# for all ips in ips.txt file
count=1
for myip in `cat ips.txt`
do

command="export LD_LIBRARY_PATH=~/AT/AugmentedTimePython/AT-ZMQ/lib"
echo "$command" > command.sh

command="sudo killall -9 peer"
echo "$command" >> command.sh

command="exit"
echo "$command" >> command.sh

cert=`cat data.txt |grep "$myip "|awk '{print $2}'`
ssh -t -t -i cert/$cert ubuntu@$myip < command.sh
rm command.sh

count=$((count + 1))
done

rm ips.txt
