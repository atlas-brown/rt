
#!/bin/sh

# Define the directory and file extension
directory="/path/to/directory"
extension=".txt"

# Use the find command to search for files with the specified extension
find "$directory" -type f -name "*$extension" | while read file
do
  # Perform any desired actions on the files
  echo "Found file: $file"
  # Add your actions here
done
