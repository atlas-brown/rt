# @output "([0-9]+:){9}[0-9]+"
yes | head -n10 | grep -n . | cut -d: -f1 | paste
