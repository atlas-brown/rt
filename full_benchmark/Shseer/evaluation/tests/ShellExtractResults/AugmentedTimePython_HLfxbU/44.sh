#!/bin/sh

cat data.txt |awk '{print $1}' > ips.txt

# for all ips in ips.txt file
count=1
for myip in `cat ips.txt`
do

command="export LD_LIBRARY_PATH=~/AT/AugmentedTimePython/AT-ZMQ/lib"
echo "$command" > command.sh

command="cd ~/AT/AugmentedTimePython/Socket/;git reset --hard c44c5d928f589419479d469df86adb643c099ee1;rm events.log nohup.out;make"
echo "$command" >> command.sh

command="nohup ./peer $count"
for i in `cat ips.txt`
do
    if [ $myip != $i ]
    then
        command="$command $i:12345"
    fi
done
echo "$command 1> nohup.out 2> nohup.out &" >> command.sh

command="exit"
echo "$command" >> command.sh

cert=`cat data.txt |grep "$myip "|awk '{print $2}'`
ssh -t -t -i cert/$cert ubuntu@$myip < command.sh
rm command.sh

count=$((count + 1))
done

rm ips.txt
