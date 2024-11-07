
#!/bin/sh

# Check if the user has provided the correct number of command line arguments
if [ $# -ne 2 ]; then
  echo "Usage: $0 <directory> <compressed_file_name>"
  exit 1
fi

# Compress the directory into a tar.gz file
tar -czvf $2.tar.gz $1
