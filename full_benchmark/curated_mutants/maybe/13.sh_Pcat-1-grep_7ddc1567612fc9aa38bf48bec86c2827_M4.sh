# @assume "cat ${1}" --> ".*"
# @output "hello, world"
cat ${1} | cut -d "\"" -f 2 | cut -c 1-12
