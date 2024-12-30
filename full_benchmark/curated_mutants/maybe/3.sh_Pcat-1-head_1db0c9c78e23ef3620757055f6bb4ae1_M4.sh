# @assume "cat $1" --> "[A-Za-z-']+ [A-Za-z-']+"
# @output "[A-Za-z-']+"
cat ${1} | head -n 2
