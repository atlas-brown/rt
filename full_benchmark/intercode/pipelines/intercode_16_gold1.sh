# Query: Count all the lines of all '*.c' files in /testbed directory recursively

find /testbed -name "*.c" -print0 | xargs -0 cat | wc -l