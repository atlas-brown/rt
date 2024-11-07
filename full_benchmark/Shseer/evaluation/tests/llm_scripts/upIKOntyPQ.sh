
#!/bin/sh

echo "Enter a number or string: "
read input

if [ "$input" -eq "$input" ] 2>/dev/null; then
  echo "Valid number input: $input"
else
  echo "Valid string input: $input"
fi
