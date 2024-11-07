
#!/bin/bash

# Set the threshold size for identifying large files and directories
threshold=100M

# Use the du command to find the size of directories
large_directories=$(du -h /path/to/directory/* | awk -v threshold="$threshold" '$1 > threshold {print $2}')

# Use the rm command to delete large files and directories
for item in $large_directories
do
    if [ -f "$item" ]; then
        rm "$item"  # Delete large files
    elif [ -d "$item" ]; then
        rm -r "$item"  # Delete large directories
    fi
done
