
#!/bin/bash

# Check if the CSV file is provided as an argument
if [ $# -ne 1 ]; then
  echo "Usage: $0 <csv_file>"
  exit 1
fi

# Read the CSV file and count the number of rows and columns
rows=$(cat $1 | wc -l)
columns=$(head -n 1 $1 | tr ',' '\n' | wc -l)

# Output the result
echo "Number of rows: $rows"
echo "Number of columns: $columns"
