# @output "[0-9]+"
cat ${1} | tr " " "\\n" | grep "\\." | wc
