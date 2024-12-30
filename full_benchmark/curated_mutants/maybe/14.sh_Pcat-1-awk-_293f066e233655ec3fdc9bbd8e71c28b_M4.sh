# @assume "cat ${1}" --> "[A-Z][a-z]+ [0-9.]+"
cat ${1} | sort -nr | cut -d " " -f 2
