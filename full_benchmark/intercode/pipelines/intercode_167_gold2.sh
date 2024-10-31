# Query: Print source of the file system containing current working directory.

df -P . | awk 'NR==2 {print $1}'