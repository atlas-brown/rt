
#!/bin/sh

# Check if the correct number of arguments are provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <original_directory_name> <new_directory_name>"
  exit 1
fi

# Rename the directory
mv "$1" "$2"
