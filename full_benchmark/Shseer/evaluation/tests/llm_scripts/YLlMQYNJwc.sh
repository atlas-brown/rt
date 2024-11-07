
#!/bin/sh

# Check if the directory path is provided as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <directory_path>"
  exit 1
fi

# Use find command to list all files in the directory and its subdirectories
file_count=$(find "$1" -type f | wc -l)

echo "Number of files in $1 and its subdirectories: $file_count"
