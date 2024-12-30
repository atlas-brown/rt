# Query: List environment variables and their values, escaping all semicolons with a backslash.

# @assume "env" --> "[A-Za-z0-9_]+=.*"
# @output "[A-Za-z0-9_]+=((.*)&((?!(.*[^\\];.*))))"
env | sed 's/;/\\;/g'
