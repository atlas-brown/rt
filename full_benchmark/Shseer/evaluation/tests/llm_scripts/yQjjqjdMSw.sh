
#!/bin/sh

# Check if the correct number of arguments are provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <old_directory> <new_directory>"
  exit 1
fi

# Rename the directory
mv "$1" "$2"

# Move all files and subdirectories to the new directory
mv "$2"/* "$2"/.[!.]* "$2"/..?* "$2" 2>/dev/null
