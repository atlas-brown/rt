# Query: Create an empty file "abc.txt" in each directory named "dir1" under testbed directory.

find /testbed -type d -name "dir1" -print |  sed 's/$/\/abc.txt/g' | xargs touch