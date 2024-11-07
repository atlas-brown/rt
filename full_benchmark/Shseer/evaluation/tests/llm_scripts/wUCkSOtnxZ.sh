
#!/bin/sh

# Check if the correct number of command line arguments are provided
if [ "$#" -ne 3 ]; then
  echo "Usage: $0 input_file chunk_size output_file_prefix"
  exit 1
fi

input_file=$1
chunk_size=$2
output_file_prefix=$3

# Calculate the number of chunks
file_size=$(wc -c < "$input_file")
num_chunks=$((file_size / chunk_size))

# Split the input file into smaller chunks
split -b "$chunk_size" "$input_file" "$output_file_prefix"

echo "File split into $num_chunks chunks"
