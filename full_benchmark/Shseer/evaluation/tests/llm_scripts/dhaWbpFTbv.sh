
#!/bin/sh

# Check if the directory is empty
if [ -z "$(ls -A /path/to/directory)" ]; then
  # If the directory is empty, remove it
  rmdir -p /path/to/directory
  echo "Directory removed successfully"
else
  # If the directory is not empty, do not remove it
  echo "Directory is not empty, cannot remove"
fi
