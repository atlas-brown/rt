# @output "[A-Z]+"
cat ${1} | tr -c "[a-z][A-Z]" "\\n" | grep "[A-Z]" | sed 1d | sed 2d | sed 3d | sed 4d | tr -d "\\n" | tr -c "[A-Z]" "\\n"
