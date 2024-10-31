# Query: Search for the system host name in "/etc/hosts" and print the IP address in the first awk field

grep "$(hostname)" /etc/hosts | awk '{print $1}'