# @assume "cat $1" --> "[A-Za-z-']+ [A-Za-z-']+"
# @output "(?!(.* .*))"
cat ${1} | sort
