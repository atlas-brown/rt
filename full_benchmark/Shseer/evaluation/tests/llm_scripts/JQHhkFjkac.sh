
#!/bin/sh

# Define the log file
logfile="example.log"

# Define the patterns to search for
patterns=("error" "warning" "info")

# Loop through each pattern
for pattern in "${patterns[@]}"
do
  # Count the occurrences of the pattern in the log file
  count=$(grep -c "$pattern" "$logfile")

  # Print the count of occurrences
  echo "Occurrences of $pattern: $count"

  # Extract specific information from the matching lines
  grep "$pattern" "$logfile" | awk '{print $1, $3}'  # Example: Extracting the first and third column
done
