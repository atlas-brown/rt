# Query: Print the total disk usage in bytes of all files listed in "/workspace/files.txt"

awk '{print $0}' /workspace/files.txt | xargs du -b | awk '{sum += $1} END {print sum}'