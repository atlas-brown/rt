# Query: Count number of users logged in

who | awk -F' ' '{print $1}' | sort -u | wc -l