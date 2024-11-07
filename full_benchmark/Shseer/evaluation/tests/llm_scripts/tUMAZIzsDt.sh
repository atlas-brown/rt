
#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <permissions> <directory_path>"
  exit 1
fi

# Store the arguments in variables
permissions=$1
directory_path=$2

# Use the find command to search for all directories within the specified directory
find "$directory_path" -type d -exec chmod "$permissions" {} \;
