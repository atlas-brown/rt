# Query: Calculate a list of duplicate md5 sum hashes for all the ".java" files in the /testbed directory

md5sum /testbed/*.java | awk '{print $1}' | sort | uniq -d