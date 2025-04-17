# @file "$1": "BBCD ABCD\nQWER WERT03214\nLKJHGF KJHGFD\n"
# @output "awk"
cat ${1} | cut -d " " -f 2 | cut -c 1-1 | tr "[A-Z]" "[a-z]"
