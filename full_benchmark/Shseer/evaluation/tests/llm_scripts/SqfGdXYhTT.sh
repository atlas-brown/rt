
#!/bin/sh

# Prompt the user for input
echo "Please enter a number or string: "
read input

# Validate the input for number
if [ "$input" -eq "$input" ] 2>/dev/null; then
  echo "Valid number input: $input"
else
  # Validate the input for string
  if [ -n "$input" ] && [ -z "${input//[A-Za-z]/}" ]; then
    echo "Valid string input: $input"
  else
    echo "Invalid input: $input is neither a number nor a string"
  fi
fi
