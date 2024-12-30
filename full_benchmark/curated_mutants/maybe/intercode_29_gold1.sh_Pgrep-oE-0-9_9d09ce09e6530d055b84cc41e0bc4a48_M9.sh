# @output "[0-9]+ +([0-9]{1,3}\.){3}[0-9]{1,3}"
grep -oE /etc/networks | sort | uniq -c | sort -nr
