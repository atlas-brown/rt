# Query: Print the 3 largest directories in /workspace.

# @assume "du -a /workspace" --> "([0-9]+[ \t]+[^\n]+\n)+"
du -a /workspace | sort -nr | head -n 3
