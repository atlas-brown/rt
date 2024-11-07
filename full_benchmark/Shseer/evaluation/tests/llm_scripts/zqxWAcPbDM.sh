
#!/bin/sh

read -p "Enter a number, string, or date: " userInput

if [ "$userInput" -eq "$userInput" ] 2>/dev/null; then
    echo "Valid number"
else
    echo "Invalid number"
fi

if [[ $userInput =~ ^[a-zA-Z]+$ ]]; then
    echo "Valid string"
else
    echo "Invalid string"
fi

if [[ $userInput =~ ^[0-9]{2}-[0-9]{2}-[0-9]{4}$ ]]; then
    echo "Valid date"
else
    echo "Invalid date"
fi
