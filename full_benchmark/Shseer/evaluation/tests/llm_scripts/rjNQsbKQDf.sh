
#!/bin/sh

# Define the directory to search
directory="/path/to/directory"

# Use the find command to search for files with specific permissions
find $directory -type f -perm /specific_permissions -exec ls -l {} \;
