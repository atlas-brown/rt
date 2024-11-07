
#!/bin/sh

# Check if the correct number of command line arguments are provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 file1 file2"
  exit 1
fi

# Compare the two files using the diff command
diff "$1" "$2"
