# @file "$1": "([A-Za-z ]+\.){3}[A-Za-z ]+|[0-9]+"
# @output "[A-Z]*"
cat ${1} | tr " " "\\n" | cut -d "." -f 2 | cut -c 1-1 | tr "[a-z]" "P" | sort -r | uniq | head -n 3 | tail -n 1