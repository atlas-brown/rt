
#!/bin/sh

# Check if the correct number of arguments are provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <directory> <file_extension>"
  exit 1
fi

# Store the directory and file extension from command line arguments
directory=$1
file_extension=$2

# Use the find command to search for files with the specified extension in the directory
find "$directory" -type f -name "*.$file_extension"
