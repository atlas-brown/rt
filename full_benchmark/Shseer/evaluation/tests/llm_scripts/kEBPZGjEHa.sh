#!/bin/sh

url=$1

# Validate URL format
if [[ $url =~ ^https?:// ]]; then
    echo "Valid URL format"
else
    echo "Invalid URL format"
fi

# Check if URL is reachable
ping -c 1 $url

# Return status code of the response
curl -s -o /dev/null -w "%{http_code}" $url