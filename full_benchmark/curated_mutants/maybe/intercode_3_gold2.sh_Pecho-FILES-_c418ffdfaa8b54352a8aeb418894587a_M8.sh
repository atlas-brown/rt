# @output "[a-z0-9]{33} -"
echo "${FILES}" | tr " " "\\n" | sort | xargs cat
