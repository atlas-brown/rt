# Query: Remove the last 3 characters from "987654321"

# @assume "echo \"987654321\"" --> "987654[0-9]{3}"
echo "987654321" | sed 's/...$//'
