# Query: Count number of users logged in

# @output " *[0-9]+"
who | awk -F' ' '{print $1}' | sort -u | wc -l
