
#!/bin/bash

# Loop through all .tar.gz files in the directory
for file in *.tar.gz; do
  # Create a directory for each archive
  dir_name=$(basename "$file" .tar.gz)
  mkdir "$dir_name"

  # Extract specific files from the archive
  tar -xzf "$file" -C "$dir_name" file1.txt file2.txt

  # Organize the extracted files into separate directories based on their file types
  mkdir "$dir_name"/txt_files
  mv "$dir_name"/*.txt "$dir_name"/txt_files
done
