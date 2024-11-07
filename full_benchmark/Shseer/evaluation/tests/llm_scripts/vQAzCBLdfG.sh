
#!/bin/sh

# Read the content of each text file
file1_content=$(cat file1.txt)
file2_content=$(cat file2.txt)
file3_content=$(cat file3.txt)

# Append the content to a new text file
echo "$file1_content" > combined_files.txt
echo "$file2_content" >> combined_files.txt
echo "$file3_content" >> combined_files.txt

echo "Text files have been successfully combined into combined_files.txt"
