# Query: Calculate the md5 sum of the contents of the sorted list of files "$FILES"
# @assert "md5sum" --> "[a-z0-9]{33}  -"
# @var "$FILES": "([a-z]+ )+"
cat $(echo $FILES | tr ' ' '\n' | sort) | md5sum
