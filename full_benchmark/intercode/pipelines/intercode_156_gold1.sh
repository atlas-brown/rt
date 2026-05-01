# Query: Extract host name part from "http://www.google.com"

# @assume "echo \"http://www.google.com\"" --> "http://www\.[a-z]+\.com"
echo "http://www.google.com" | cut -d'/' -f3
