
#!/bin/sh

# Check if the user has provided the directory name or path
if [ $# -ne 1 ]; then
  echo "Usage: $0 <directory_name>"
  exit 1
fi

# Remove the directory using rmdir or rm -r
if [ -d "$1" ]; then
  rmdir "$1" || rm -r "$1"
  echo "Directory $1 has been removed"
else
  echo "Directory $1 does not exist"
fi
