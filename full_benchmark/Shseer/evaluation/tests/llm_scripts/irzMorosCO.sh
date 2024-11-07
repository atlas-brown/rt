
#!/bin/sh

# Check if a new name is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <new_name>"
  exit 1
fi

# Rename the current working directory
mv "$(pwd)" "$1"

echo "Current working directory renamed to $1"
