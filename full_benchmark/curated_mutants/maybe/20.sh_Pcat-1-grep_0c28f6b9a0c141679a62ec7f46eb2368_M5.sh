# @assume "cat ${1}" --> ".*"
cat ${1} | cut -d "(" -f 2 | cut -d ")" -f 1 | head -n 1
