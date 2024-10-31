# Query: Extract host name part from "http://www.google.com"

echo "http://www.google.com" | sed -E 's|https?://([^/]+).*|\1|'