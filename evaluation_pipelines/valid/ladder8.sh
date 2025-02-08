# previous annotation:
# @output "3|4|5"

# @output "[+-]?[0-9]+"
seq 10 | head -3 | xargs -n 1 expr 2 +
