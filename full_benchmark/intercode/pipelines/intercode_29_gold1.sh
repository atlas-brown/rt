# Query: Counts number of occurences of all ip addresses in '/etc/networks' file, and prints all addresses with number of occurences in a descending order.

grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' /etc/networks | sort | uniq -c | sort -nr