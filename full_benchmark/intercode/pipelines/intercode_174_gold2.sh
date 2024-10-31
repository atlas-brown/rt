# Query: Extract, sort and print only group names from /etc/group.

cut -d: -f1 /etc/group | sort | uniq