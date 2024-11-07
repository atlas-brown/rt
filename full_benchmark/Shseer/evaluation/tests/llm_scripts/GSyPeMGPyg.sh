
#!/bin/sh

# Check if the correct number of arguments are provided
if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <directory> <file_extension> <excluded_directories>"
  exit 1
fi

directory="$1"
file_extension="$2"
excluded_directories="$3"

# Use the find command to search for files with the specified extension while excluding certain directories
find "$directory" -type f -name "*.$file_extension" -not -path "*/$excluded_directories/*"
