# Query: List all variables (names only) with names containing "H".

env | grep '^[^=]*H[^=]*=' | awk -F= '{print $1}'