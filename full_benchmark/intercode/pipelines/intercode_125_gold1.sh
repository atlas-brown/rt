# Query: Calculate the md5 sum of all files in directory tree "/workspace"

find /workspace -type f -exec md5sum {} + | sort