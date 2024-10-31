# Query: Print a list of unique users who are logged in

who | awk '{print $1}' | sort | uniq