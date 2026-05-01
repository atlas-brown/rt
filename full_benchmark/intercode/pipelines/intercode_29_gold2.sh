# Query: Counts number of occurences of all ip addresses in '/etc/networks' file, and prints all addresses with number of occurences in a descending order.

awk '{for (i=1; i<=NF; i++) if ($i ~ /([0-9]{1,3}\.){3}[0-9]{1,3}/) print $i}' /etc/networks | sort | uniq -c | sort -nr