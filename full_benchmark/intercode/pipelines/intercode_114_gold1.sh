# Query: prints the last non-empty line of "/workspace/dir1/a.txt"

tac /workspace/dir1/a.txt | grep -m 1 '.'