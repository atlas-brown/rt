# @assume "cat $1" --> "[A-Z][a-z]+ [A-Z][A-Za-z]+"
# @expect "[0-9]+ +[A-Z][a-z]+" --> "sort -r"
cat ${1} | cut -d " " -f 1 | sort | uniq | sort -r
