
#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -ne 3 ]; then
  echo "Usage: $0 input_file pattern output_name"
  exit 1
fi

input_file=$1
pattern=$2
output_name=$3

# Check if the input file exists
if [ ! -f "$input_file" ]; then
  echo "Input file does not exist"
  exit 1
fi

# Create a directory to store the output files
mkdir -p output

# Split the file based on the pattern
csplit -z "$input_file" "/$pattern/" "{*}"

# Rename the output files based on the naming convention
count=1
for file in xx*; do
  mv "$file" "output/${output_name}_${count}"
  ((count++))
done

echo "File split complete"
