# @assume "cat $1" --> "Any Grouping by this fRiend,\nMakes each sentence quickly clear!\nTop and bottom, either end,\nSpacE-in five -- see friend apPear!"
# @output "GREP"
cat ${1} | grep "[A-Z]" | tr " " "\\n" | sed 1d | sed 3d | sed 3d | tr "[a-z]" "\\n" | grep "[A-Z]" | sed 3d | tr -c "[A-Z]" "\\n" | tr -d "\\n"
