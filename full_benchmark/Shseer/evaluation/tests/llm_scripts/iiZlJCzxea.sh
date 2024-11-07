
#!/bin/sh

# Check if two directory paths are provided as command line arguments
if [ $# -ne 2 ]; then
  echo "Usage: $0 <directory1> <directory2>"
  exit 1
fi

# Function to recursively list all files and subdirectories in a directory
list_files() {
  local dir="$1"
  find "$dir" -type f -exec ls -l {} + | awk '{print $9, $5, $3, $1}'
  find "$dir" -type d -exec ls -ld {} + | awk '{print $9, $3, $1}'
}

# Compare the lists of files and subdirectories in each directory
dir1_files=$(list_files "$1")
dir2_files=$(list_files "$2")

echo "Files and subdirectories in $1:"
echo "$dir1_files"

echo "Files and subdirectories in $2:"
echo "$dir2_files"

# Compare the lists to identify any differences
diff <(echo "$dir1_files") <(echo "$dir2_files")
