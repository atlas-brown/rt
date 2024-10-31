# Query: Count the total number of lines in all "*.gz" files in the /testbed directory tree after decompression

find /testbed -type f -name '*.gz' | xargs zcat | wc -l