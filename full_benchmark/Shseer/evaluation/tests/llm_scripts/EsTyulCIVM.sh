
#!/bin/sh

file_to_remove="example.txt"

if [ -f "$file_to_remove" ]; then
  rm "$file_to_remove"
  echo "File $file_to_remove removed successfully"
else
  echo "File $file_to_remove does not exist"
fi
