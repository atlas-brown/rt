
#!/bin/sh

# Function to validate URL format
validate_url() {
  url=$1
  if echo "$url" | grep -E -q '^(http|https)://[^ "]+$'; then
    return 0
  else
    return 1
  fi
}

# Function to check if URL is reachable and return status code
check_url_status() {
  url=$1
  status_code=$(curl -s -o /dev/null -w "%{http_code}" $url)
  echo "Status code for $url: $status_code"
}

# Main script
read -p "Enter the URL to validate and check status: " input_url

if validate_url "$input_url"; then
  echo "URL format is valid"
  check_url_status "$input_url"
else
  echo "Invalid URL format"
fi
