# Query: Print a list of unique users who are logged in

who | cut -d' ' -f1 | sort | uniq