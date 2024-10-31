# Query: Counts total number of only lines with alphanumeric symbols in all *.php files in the /testbed folder and subfolders.

find /testbed -type f -name '*.php' -exec grep -H '.*[[:alnum:]].*' {} + | wc -l