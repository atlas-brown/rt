# @output "[0-9]+"
cat ${1} | tr " " "\\n" | grep "x" | grep "\\." | wc
