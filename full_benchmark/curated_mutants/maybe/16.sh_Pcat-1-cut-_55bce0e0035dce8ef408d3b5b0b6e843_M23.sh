
# @file "$1": "[a-zA-Z0-9]+\t[0-9]+"
# @output "[0-9]+"
cat ${1} | cut -f 2 | sort -n | uniq | sort -nr | head -n 1 | tr -s " " "\\n" | tail -n 1