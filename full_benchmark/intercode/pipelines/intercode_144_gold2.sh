# Query: Print percentage of the space used on the /workspace directory.

df -h /workspace | awk 'NR==2 {print $5}'