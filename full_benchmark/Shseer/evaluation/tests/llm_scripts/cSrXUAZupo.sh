
#!/bin/sh

# Prompt user for input
read -p "Enter a number: " number
read -p "Enter a string: " string
read -p "Enter a date (YYYY-MM-DD): " date

# Validate number
if ! [[ $number =~ ^[0-9]+$ ]]; then
  echo "Invalid number input"
fi

# Validate string
if ! [[ $string =~ ^[a-zA-Z]+$ ]]; then
  echo "Invalid string input"
fi

# Validate date
if ! [[ $date =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "Invalid date input"
fi

# Check number range
if [ $number -lt 0 ] || [ $number -gt 100 ]; then
  echo "Number must be between 0 and 100"
fi

# Check string length
if [ ${#string} -gt 10 ]; then
  echo "String must be 10 characters or less"
fi

# Check date format
if ! date -d "$date" >/dev/null 2>&1; then
  echo "Invalid date format"
fi

echo "Input validation complete"
