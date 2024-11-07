
#!/bin/sh

# Set the directory to search in
search_dir="/path/to/search/directory"

# Set the specific extension to search for
file_extension=".txt"

# Set the directories to exclude from the search
exclude_dirs="dir1 dir2 dir3"

# Use the find command to search for files with the specific extension and exclude certain directories
find "$search_dir" -type f -name "*$file_extension" -not -path "*/$exclude_dirs/*"
