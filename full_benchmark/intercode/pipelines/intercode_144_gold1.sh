# Query: Print percentage of the space used on the /workspace directory.

df -k /workspace | tail -1 | awk '{print $5}'