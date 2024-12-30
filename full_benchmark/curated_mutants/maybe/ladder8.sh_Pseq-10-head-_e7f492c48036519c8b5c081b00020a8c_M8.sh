# @output "3|4|5"
seq 10 | head | xargs -n 1 expr 2 +
