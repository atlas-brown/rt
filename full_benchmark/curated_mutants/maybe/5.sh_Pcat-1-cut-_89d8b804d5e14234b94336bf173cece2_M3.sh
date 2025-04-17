# @file "$1": "[A-Z]+ is a [a-z,]+, (and|\\.)"
# @output "[a-z]*"
cat ${1} | tr -d ","
