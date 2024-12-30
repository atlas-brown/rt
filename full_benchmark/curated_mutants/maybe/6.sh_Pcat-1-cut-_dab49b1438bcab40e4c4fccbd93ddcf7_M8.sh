# @assume "cat $1" --> "[A-Za-z]+ [A-Za-z]+"
# @output "awk"
cat ${1} | cut -d " " -f 2 | cut -c 1-1 | tr -d "\\n"
