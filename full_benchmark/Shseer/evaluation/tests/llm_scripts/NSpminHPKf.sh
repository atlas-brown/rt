
#!/bin/sh

# Check if the user has provided the pattern and new permissions
if [ $# -ne 2 ]; then
  echo "Usage: $0 <pattern> <permissions>"
  exit 1
fi

# Store the pattern and permissions in variables
pattern=$1
permissions=$2

# Use the find command to locate the files and directories that match the pattern
find . -name "$pattern" -exec chmod $permissions {} \;
