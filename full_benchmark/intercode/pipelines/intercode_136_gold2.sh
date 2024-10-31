# Query: Counts lines in file /workspace/dir1/a.txt ignoring empty lines and lines with spaces only.

grep -v '^[[:space:]]*$' /workspace/dir1/a.txt | wc -l