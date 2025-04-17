# Query: Counts total number of only lines with alphanumeric symbols in all *.php files in the /testbed folder and subfolders.

find /testbed -name '*.php' | xargs cat | awk '/[a-zA-Z0-9]/ {i++} END{print i}'