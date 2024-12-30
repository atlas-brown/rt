# @assume "cat ${1}" --> ".*"
# @output "[A-Za-z,\\. ]"
cat ${1} | grep "(" | cut -d "(" -f 2 | head -n 1
