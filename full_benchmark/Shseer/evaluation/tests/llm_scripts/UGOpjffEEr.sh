
#!/bin/bash

# Set the threshold size in megabytes
threshold=100

# Create a log file to record deleted files and directories
log_file="cleanup_log.txt"
touch $log_file

# Identify and delete large files
find /path/to/search -type f -size +${threshold}M -exec rm -f {} \; -exec echo "Deleted file: {}" >> $log_file \;

# Identify and delete large directories
find /path/to/search -type d -size +${threshold}M -exec rm -rf {} \; -exec echo "Deleted directory: {}" >> $log_file \;

echo "Disk cleanup complete. Deleted files and directories logged in $log_file"
