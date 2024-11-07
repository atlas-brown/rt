
#!/bin/sh

# Check if the correct number of arguments is provided
if [ $# -lt 3 ]; then
    echo "Usage: $0 <directory> <compressed_file_name> <excluded_items...>"
    exit 1
fi

# Create the compressed file
tar -cvf $2 $1 --exclude=$3
