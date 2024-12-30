# @assume "cat $1" --> "[A-Z] is[A-Za-z,](, and|\\.)"
# @output "[a-z]+"
cat ${1} | tr -d ","
