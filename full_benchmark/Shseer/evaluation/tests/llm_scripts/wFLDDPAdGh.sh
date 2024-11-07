
#!/bin/sh

# Check if two directory paths are provided as command line arguments
if [ $# -ne 2 ]; then
  echo "Usage: $0 <directory1> <directory2>"
  exit 1
fi

# Assign the directory paths to variables
dir1=$1
dir2=$2

# List the files in each directory
files_dir1=$(ls -p $dir1 | grep -v /)
files_dir2=$(ls -p $dir2 | grep -v /)

# Compare the lists to identify any differences in the file contents
echo "Files in $dir1:"
echo "$files_dir1"
echo "Files in $dir2:"
echo "$files_dir2"
echo "Differences in file contents:"
diff <(echo "$files_dir1") <(echo "$files_dir2")
