# @output "[_a-z][-0-9_a-z]*[$]?"
cut -f1 /etc/group | sort | uniq
