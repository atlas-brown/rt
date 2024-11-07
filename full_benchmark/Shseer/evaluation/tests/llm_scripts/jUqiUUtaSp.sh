
#!/bin/sh

# Check if URL argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <URL>"
  exit 1
fi

# Regular expression to validate URL format
url_regex="^(http|https)://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}(/.*)?$"

# Check if the URL matches the regular expression
if [[ $1 =~ $url_regex ]]; then
  echo "Valid URL"
else
  echo "Invalid URL"
fi
