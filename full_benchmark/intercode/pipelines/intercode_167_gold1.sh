# Query: Print source of the file system containing current working directory.

df . | tail -1 | awk '{print $1}'