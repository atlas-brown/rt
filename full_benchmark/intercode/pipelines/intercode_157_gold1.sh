# Query: List environment variables and their values, escaping all semicolons with a backslash.

env | sed 's/;/\\;/g'