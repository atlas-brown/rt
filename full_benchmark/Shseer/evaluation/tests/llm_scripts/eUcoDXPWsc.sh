
#!/bin/sh

# Check if the log file is provided as an argument
if [ $# -ne 1 ]; then
  echo "Usage: $0 <log_file>"
  exit 1
fi

log_file=$1
pattern="ERROR"  # Replace with the specific pattern to search for

# Search for the pattern in the log file and display matching lines
grep "$pattern" "$log_file"
