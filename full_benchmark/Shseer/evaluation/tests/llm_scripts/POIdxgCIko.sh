
#!/bin/sh

# Check if at least one directory is provided as a command line argument
if [ $# -eq 0 ]; then
  echo "Usage: $0 directory1 [directory2 ...]"
  exit 1
fi

# Iterate through each directory provided as a command line argument
for dir in "$@"; do
  # Check if the directory exists
  if [ -d "$dir" ]; then
    # List the contents of the directory
    echo "Contents of $dir:"
    ls -l "$dir"
  else
    echo "Error: $dir is not a directory"
  fi
done
