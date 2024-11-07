
#!/bin/bash

# Specify the directory and the date
directory="/path/to/directory"
date="2022-01-01"

# Find files older than the specified date
find $directory -type f -mtime +30 -exec mv {} /tmp/ \;
