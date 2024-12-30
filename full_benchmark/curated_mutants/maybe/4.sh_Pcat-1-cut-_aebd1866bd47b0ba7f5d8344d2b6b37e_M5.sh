# @assume "cat $1" --> "[A-Z][a-z]+ [A-Z][A-Za-z]+"
# @expect "[A-Z][a-z]+" --> "sort"
cat ${1} | sort | uniq -c | sort -r
