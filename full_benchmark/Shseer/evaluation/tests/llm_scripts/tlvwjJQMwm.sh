
#!/bin/bash

# Set the directory path
directory="/path/to/directory"

# Set the output file name
output_file="output.txt"

# Exclude files with a specific file extension
excluded_extension=".exclude"

# Change to the directory
cd $directory

# Find all text files in the directory, excluding files with the specific file extension
find . -type f ! -name "*$excluded_extension" -exec cat {} + > $output_file

echo "All text files have been concatenated into $output_file"
