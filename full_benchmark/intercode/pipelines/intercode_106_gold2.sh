# Query: List the details of all the text files in /workspace directory.

find /workspace -name "*.txt" | xargs ls -ld