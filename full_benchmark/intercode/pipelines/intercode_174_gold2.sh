# Query: Extract, sort and print only group names from /etc/group.

# @output "[_a-z][-0-9_a-z]*[$]?"
cut -d: -f1 /etc/group | sort | uniq
