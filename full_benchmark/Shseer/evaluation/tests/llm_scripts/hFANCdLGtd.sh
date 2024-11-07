
#!/bin/sh

# Check if the directory path is provided as a command line argument
if [ $# -ne 1 ]; then
  echo "Usage: $0 <directory_path>"
  exit 1
fi

# Store the directory path from the command line argument
directory_path=$1

# Use ls to list all the files in the directory and wc to count the number of files
file_count=$(ls -l $directory_path | grep "^-" | wc -l)

echo "Number of files in $directory_path: $file_count"
