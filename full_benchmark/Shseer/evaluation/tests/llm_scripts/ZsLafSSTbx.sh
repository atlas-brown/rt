
#!/bin/sh

# Check if the correct number of arguments are provided
if [ $# -ne 2 ]; then
  echo "Usage: $0 <permissions> <file/directory>"
  exit 1
fi

# Assign the command line arguments to variables
permissions=$1
file_or_directory=$2

# Change the permissions of the file or directory
chmod $permissions $file_or_directory

# Check if the permissions were successfully changed
if [ $? -eq 0 ]; then
  echo "Permissions changed successfully for $file_or_directory"
else
  echo "Failed to change permissions for $file_or_directory"
fi
