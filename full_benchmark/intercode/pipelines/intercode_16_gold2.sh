# Query: Count all the lines of all '*.c' files in /testbed directory recursively

find /testbed -name "*.c" -exec wc -l {} + | awk '{s+=$1} END {print s}'