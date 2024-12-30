# @output "[0-9]+"
cat ${1} | tr " " "\\n" | grep "x" | grep "\\." | cut -d "." -f 2 | grep -v "[KQRBN]" | wc
