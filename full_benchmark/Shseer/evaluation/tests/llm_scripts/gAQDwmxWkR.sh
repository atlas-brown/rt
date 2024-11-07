
#!/bin/bash

# Specify the directory to change permissions
directory="/path/to/directory"

# Exclude certain subdirectories or files
exclude_dir="/path/to/exclude/dir"
exclude_file="/path/to/exclude/file"

# Log file for auditing purposes
log_file="permission_changes.log"

# Use find command to recursively find all files and directories within the specified directory
find "$directory" -type d -name "$exclude_dir" -prune -o -type f -name "$exclude_file" -prune -o -exec chmod 644 {} \; >> "$log_file"
