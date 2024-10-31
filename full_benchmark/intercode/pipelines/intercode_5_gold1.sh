# Query: Calculate the total disk usage for each ".txt" file on the /testbed directory and prepend the system host name to the output

find /testbed -name "*.txt" -exec du {} + | awk -v hostname="$(hostname)" '{print hostname, $0}'