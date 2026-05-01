# Query: List environment variables and their values, escaping all semicolons with a backslash.

# @assume "env" --> "[A-Za-z0-9_]+=.*"
# @assume "sed 's/;/\\\\;/g'" --> "[A-Za-z0-9_]+=.*"
env | sed 's/;/\\;/g'
