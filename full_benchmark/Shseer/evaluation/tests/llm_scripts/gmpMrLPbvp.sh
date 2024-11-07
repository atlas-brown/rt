
#!/bin/sh

# Set the directory and date
directory="/path/to/directory"
date="2022-01-01"

# Identify files older than the specified date and categorize them based on file type
find "$directory" -type f -mtime +30 | while read file; do
    file_type=$(file -b --mime-type "$file")
    mkdir -p "/tmp/$file_type"
    mv "$file" "/tmp/$file_type"
done

# Prompt the user for confirmation before deleting the files
echo "Do you want to delete the files in /tmp? (y/n)"
read confirmation
if [ "$confirmation" = "y" ]; then
    rm -rf /tmp/*
    echo "Files deleted successfully"
else
    echo "Files not deleted"
fi
