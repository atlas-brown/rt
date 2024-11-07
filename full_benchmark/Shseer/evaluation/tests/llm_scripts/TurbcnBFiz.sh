
#!/bin/sh

# Check if the correct number of arguments are provided
if [ $# -ne 2 ]; then
  echo "Usage: $0 <directory> <encryption_algorithm>"
  exit 1
fi

directory=$1
algorithm=$2

# Loop through all the files in the directory
for file in $directory/*; do
  # Check if the file is a regular file
  if [ -f "$file" ]; then
    # Encrypt the file using the specified algorithm
    openssl enc -$algorithm -in "$file" -out "$file.enc"
    # Remove the original file
    rm "$file"
  fi
done

echo "Encryption complete"
