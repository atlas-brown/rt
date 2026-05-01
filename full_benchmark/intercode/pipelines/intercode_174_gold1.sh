# Query: Extract, sort and print only group names from /etc/group.
# @output "[_a-z][-0-9_a-z]*[$]?"
# @file "/etc/group": "[a-z]+:x:[0-9]+:"
# @assume "cut -d: -f1 /etc/group" --> "[_a-z][-0-9_a-z]*[$]?"
cut -d: -f1 /etc/group | sort
