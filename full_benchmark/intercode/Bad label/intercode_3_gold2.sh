# Query: Calculate the md5 sum of the contents of the sorted list of files "$FILES"

echo "$FILES" | tr ' ' '\n' | sort | xargs cat | md5sum