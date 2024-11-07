
#!/bin/sh

# Check if two directory paths are provided as arguments
if [ $# -ne 2 ]; then
  echo "Usage: $0 directory1 directory2"
  exit 1
fi

dir1=$1
dir2=$2

# Check if the provided paths are directories
if [ ! -d "$dir1" ] || [ ! -d "$dir2" ]; then
  echo "Error: Both arguments must be directories"
  exit 1
fi

# List all text files in both directories
files1=$(find "$dir1" -type f -name "*.txt")
files2=$(find "$dir2" -type f -name "*.txt")

# Compare each pair of files using the diff command
for file1 in $files1; do
  file2=$(echo "$file1" | sed "s|$dir1|$dir2|")
  if [ -f "$file2" ]; then
    diff -u "$file1" "$file2" >> differences_report.txt
  else
    echo "File $file1 does not exist in $dir2" >> differences_report.txt
  fi
done

# Check for files in dir2 that do not exist in dir1
for file2 in $files2; do
  file1=$(echo "$file2" | sed "s|$dir2|$dir1|")
  if [ ! -f "$file1" ]; then
    echo "File $file2 does not exist in $dir1" >> differences_report.txt
  fi
done

echo "Differences report generated in differences_report.txt"
