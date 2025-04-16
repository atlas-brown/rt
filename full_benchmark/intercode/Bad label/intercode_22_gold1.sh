# Query: Count the number of lines in all files in the /testbed directory tree that match pattern '*file*'

find /testbed/ -name '*file*' | sort | xargs wc -l