# @assume "cat $1" --> "[A-Za-z0-9.&/ ]+\t[A-Za-z0-9/-]+\t([A-Z][a-z]+)?\t19[0-9]{2}"
# @output "[0-9]0s"
cat ${1} | cut -f 4 | sort -n | uniq | sed s/\$/"0s"/
