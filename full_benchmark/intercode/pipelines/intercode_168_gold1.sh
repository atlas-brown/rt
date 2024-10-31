# Query: List all variables (names only) with names containing "H".

env | awk -F= '{if($1 ~ /H/) print $1}'