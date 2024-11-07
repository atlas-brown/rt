
#!/bin/sh

# Check if the user has provided the correct number of command line arguments
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <permissions> <directory>"
  exit 1
fi

# Set the permissions of the directory
chmod "$1" "$2"
