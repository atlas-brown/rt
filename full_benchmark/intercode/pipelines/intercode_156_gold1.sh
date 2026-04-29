# Query: Extract host name part from "http://www.google.com"

# @output "www.google.com"
# @assume "echo \"http://www.google.com\"" --> "http://www.google.com"
# @assume "cut -d'/' -f3" --> "www.google.com"
echo "http://www.google.com" | cut -d'/' -f3
