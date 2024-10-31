# Query: Print the total disk usage in bytes of all files listed in "/workspace/files.txt"

cat /workspace/files.txt | xargs du -b | tail -1 | awk '{print $1}'