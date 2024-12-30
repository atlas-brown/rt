# @output "[0-9]+"
find ${DIRECTORY} -type f -print | sed -e "s@^.*/@@" | grep "[aeiouyAEIOUY]" | wc
