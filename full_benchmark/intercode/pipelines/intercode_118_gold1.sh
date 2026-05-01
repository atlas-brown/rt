# Query: Search for all the files in the /workspace folder which are bigger than 1KB and display the biggest file.

find /workspace -type f -size +1k -exec ls -ls {} + | sort -n | tail -1