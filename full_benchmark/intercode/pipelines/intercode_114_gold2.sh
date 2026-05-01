# Query: prints the last non-empty line of "/workspace/dir1/a.txt"

awk 'NF' /workspace/dir1/a.txt | tail -n 1