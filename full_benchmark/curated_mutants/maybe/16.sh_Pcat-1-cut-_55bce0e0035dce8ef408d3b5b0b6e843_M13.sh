# @assume "cat $1" --> "[A-Za-z0-9.&/ ]+\t[A-Za-z0-9/-]+\t([A-Z][a-z]+)?\t19[0-9]{2}"
cat ${1} | cut -f 2 | sort -n | uniq -c | sort -nr | head -n 1 | tail -n 1
