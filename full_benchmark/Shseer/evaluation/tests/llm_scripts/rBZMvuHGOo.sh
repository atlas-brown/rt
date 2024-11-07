
#!/bin/sh

string=$1
sum=0

if echo "$string" | grep -q '[0-9]'; then
    numbers=$(echo "$string" | grep -o '[0-9]\+')
    for num in $numbers; do
        sum=$((sum + num))
    done
    echo "Sum of numbers in the string: $sum"
else
    echo "No numbers found in the string."
fi
