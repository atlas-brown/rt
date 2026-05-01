# Query: Print numbers 1 through 10 separated by ":"

# @output "([0-9]+:){9}[0-9]+"
# @assume "paste -sd:" --> "([0-9]+:){9}[0-9]+"
yes | head -n10 | grep -n . | cut -d: -f1 | paste -sd:
