
#!/bin/sh

# Check if the user has provided the necessary command line arguments
if [ $# -lt 3 ]; then
  echo "Usage: $0 <directory> <compressed_file_name> <exclude_list>"
  exit 1
fi

# Assign command line arguments to variables
directory=$1
compressed_file_name=$2
exclude_list=$3

# Use the tar command to compress the directory and exclude the specified files or subdirectories
tar -czf $compressed_file_name --exclude=$exclude_list $directory

echo "Compression complete. Compressed file: $compressed_file_name"
