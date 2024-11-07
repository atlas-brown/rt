
#!/bin/sh

# Check if file is provided as argument
if [ -z "$1" ]; then
  echo "Usage: $0 <filename>"
  exit 1
fi

# Check if file exists
if [ ! -f "$1" ]; then
  echo "File not found: $1"
  exit 1
fi

# Remove empty lines from the file
sed -i '/^$/d' "$1"

echo "Empty lines removed from $1"
