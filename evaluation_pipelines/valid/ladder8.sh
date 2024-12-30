# @output "3|4|5"
seq 10 | head -3 | xargs -n 1 expr 2 +
