# @assume "cat $1" --> "[A-Za-z]+ [A-Za-z]+"
# @output "awk"
cat ${1} | cut -c 1-1 | cut -d " " -f 2 | tr -d "\\n" | tr "[A-Z]" "[a-z]"
