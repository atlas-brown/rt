# Query: Extract host name part from "http://www.google.com"

# @output "www.google.com"
echo "http://www.google.com" | cut -d'/' -f3
