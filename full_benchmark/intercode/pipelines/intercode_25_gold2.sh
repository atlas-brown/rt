# Query: Count the total number of lines in all "*.gz" files in the /testbed directory tree after decompression

find /testbed -type f -name "*.gz" -exec sh -c 'gunzip -c "$0" | wc -l' {} \; | awk '{s+=$1} END {print s}'