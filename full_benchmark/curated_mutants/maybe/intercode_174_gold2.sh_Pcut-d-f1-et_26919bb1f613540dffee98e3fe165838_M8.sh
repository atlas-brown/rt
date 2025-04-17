# @output "[_a-z][-0-9_a-z]*[$]?"
# @file "/etc/group": "[a-z]+:x:[0-9]+:"
cut -d: -f1 | sort | uniq