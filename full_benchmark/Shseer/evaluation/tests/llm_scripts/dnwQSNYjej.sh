
#!/bin/sh

# Specify the directory
directory="/path/to/directory"

# Use the find command to locate all empty directories
empty_directories=$(find $directory -type d -empty)

# Loop through the empty directories and remove them
for dir in $empty_directories
do
  rmdir $dir
done

echo "Empty directories removed successfully"
