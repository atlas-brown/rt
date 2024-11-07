
#!/bin/sh

# Check if the correct number of arguments is provided
if [ $# -ne 1 ]; then
  echo "Usage: $0 <json_file>"
  exit 1
fi

# Check if the file exists
if [ ! -f $1 ]; then
  echo "File not found: $1"
  exit 1
fi

# Check if the file is a valid JSON file
if ! jq -e . >/dev/null 2>&1 < $1; then
  echo "Invalid JSON file: $1"
  exit 1
fi

# Parse and print the contents of the JSON file in a human-readable format
jq . $1
