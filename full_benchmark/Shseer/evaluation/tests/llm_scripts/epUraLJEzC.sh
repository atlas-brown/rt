
#!/bin/sh

url=$1
regex='(http|https)://[^ "]+$'
if [[ $url =~ $regex ]]; then
    echo "Valid URL"
else
    echo "Invalid URL"
fi
