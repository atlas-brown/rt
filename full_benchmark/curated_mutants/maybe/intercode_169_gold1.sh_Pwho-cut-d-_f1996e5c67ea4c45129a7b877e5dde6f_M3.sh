# source https://unix.stackexchange.com/questions/157426/what-is-the-regex-to-validate-linux-users
# @output "[a-z_]([a-z0-9_-]{0,31}|[a-z0-9_-]{0,30}\$)"
cut -d" " -f1 | sort | uniq
