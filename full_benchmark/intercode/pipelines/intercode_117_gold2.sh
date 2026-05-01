# Query: search for all the files in the  /workspace folder and sort them in the order of their depth and display the file names

find /workspace -type f | awk -F/ '{print NF, $0}' | sort -n | cut -d' ' -f2-