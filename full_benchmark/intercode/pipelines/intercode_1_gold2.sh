# Query: Calculate a list of duplicate md5 sum hashes for all the ".java" files in the /testbed directory

find /testbed -type f -name "*.java" -exec md5sum {} + | sort | uniq -w32 -d -c | sort -nr