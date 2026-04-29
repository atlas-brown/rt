# Query: Extract host name part from "http://www.google.com"

# @output "www.google.com"
# @assume "echo \"http://www.google.com\"" --> "http://www.google.com"
# @assume "sed -E \"s|https?://([^/]+).*|\\1|\"" --> "www.google.com"
echo "http://www.google.com" | sed -E 's|https?://([^/]+).*|\1|'
