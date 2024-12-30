# @assume "cat $1" --> "Under the moon or suN\nIt's what the whole world picks!\nFOUR-CORNERED, as the earth:\nIts varied programs miX!"
# @output "UNIX"
cat ${1} | sed 2d | sed 2d | tr -d "\\n"
