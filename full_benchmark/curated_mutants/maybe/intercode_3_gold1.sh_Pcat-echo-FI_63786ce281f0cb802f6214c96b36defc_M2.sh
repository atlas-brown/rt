# @output "[a-z0-9]{33} -"
cat $(echo ${FILES} | tr " " "\\n" | sort)
