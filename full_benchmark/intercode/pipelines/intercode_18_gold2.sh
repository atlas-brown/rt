# Query: Count all the lines of all php files in the /testbed directory recursively

find /testbed/ -type f -name '*.php' | xargs cat | wc -l