# Query: Calculate the md5 sum of the contents of the sorted list of files "$FILES"
# @output "[a-z0-9]{33} -"
cat $(echo $FILES | tr ' ' '\n' | sort) | md5sum
