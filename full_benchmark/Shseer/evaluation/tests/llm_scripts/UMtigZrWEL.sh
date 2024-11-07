
#!/bin/sh

# Check if the directory is provided as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

# Use du to display disk usage and sort the output by size
du -h "$1" | sort -h
