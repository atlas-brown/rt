
#!/bin/sh

# Check if the input string is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <string>"
  exit 1
fi

# Calculate the length of the input string
length=$(expr length "$1")

# Output the length of the string
echo "The length of the string is $length"
