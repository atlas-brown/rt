
#!/bin/sh

# Check if the input string contains any numbers
if echo "$1" | grep -q '[0-9]'; then
  # Extract the numbers and calculate their sum
  sum=$(echo "$1" | tr -cd '0-9' | sed 's/\(.\)/\1+/g;s/+$//' | bc)
  echo "The sum of the numbers in the string is: $sum"
else
  echo "There are no numbers in the string."
fi
