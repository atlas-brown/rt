# Query: Calculate the md5 sum of the contents of the sorted list of files "$FILES"
# @assert "md5sum" --> "[a-z0-9]{33}  -"
# @var "$FILES": "([a-z]+ )+"
# @assume "echo $FILES" --> "([a-z]+ )+"
# @assume "tr \" \" \"\\n\"" --> "([a-z]+\n)+"
# @expect "[a-z]+" --> "sort"
cat $(echo $FILES | tr ' ' '\n' | sort) | md5sum
