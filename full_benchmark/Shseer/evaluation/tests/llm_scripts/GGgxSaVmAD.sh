
#!/bin/sh

# Check if the correct number of command line arguments are provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <file_name> <encryption_algorithm>"
  exit 1
fi

file_name=$1
encryption_algorithm=$2

# Check if the file exists
if [ ! -f "$file_name" ]; then
  echo "File $file_name does not exist"
  exit 1
fi

# Encrypt the file using the specified algorithm
case $encryption_algorithm in
  "aes-256")
    openssl enc -aes-256-cbc -in "$file_name" -out "$file_name.enc"
    ;;
  "des")
    openssl enc -des-cbc -in "$file_name" -out "$file_name.enc"
    ;;
  *)
    echo "Unsupported encryption algorithm: $encryption_algorithm"
    exit 1
    ;;
esac

echo "File $file_name encrypted using $encryption_algorithm algorithm"
