# Query: Print the 3 largest directories in /workspace.

du -a /workspace | sort -nr | head -n 3