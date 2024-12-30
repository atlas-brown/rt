# Query: Print a line of 99 '=' characters
# @output "={99}"
seq -s= 100|tr -d '[:digit:]'
