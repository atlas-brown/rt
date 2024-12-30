# Query: Print the contents of "/workspace/dir1/long.txt" in reverse order

# @assume "nl /workspace/dir1/long.txt" --> "[ ]*[0-9]+  .*"
nl /workspace/dir1/long.txt | sort -nr | cut -b8-
