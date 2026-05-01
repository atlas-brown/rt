# Query: Search for the system host name in "/etc/hosts" and print the IP address in the first awk field

more /etc/hosts | grep `hostname` | awk '{print $1}'