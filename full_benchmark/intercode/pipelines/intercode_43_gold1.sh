# Query: Prints total number of lines of all *.java files in /testbed folder and subfolders.

find /testbed -name '*.java' -print0 |xargs -0 wc -l|grep 'total' |awk '{ print $1 }'