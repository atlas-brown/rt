
#!/bin/bash

# Set the directory path
directory="/path/to/directory"

# Set the pattern to match
pattern="*.txt"

# Loop through the files in the directory
for file in "$directory"/$pattern; do
  # Get the base name of the file
  base_name=$(basename "$file")
  # Rename the file with a new name
  mv "$file" "$directory/new_${base_name}"
done
