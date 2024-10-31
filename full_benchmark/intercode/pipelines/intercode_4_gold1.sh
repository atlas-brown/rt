# Query: Calculate the md5 sum of the sorted list of md5 sums of all ".py" files under /testbed/dir1/subdir1

find /testbed/dir1/subdir1 -type f -name *.py -exec md5sum {} + | awk '{print $1}' | sort | md5sum