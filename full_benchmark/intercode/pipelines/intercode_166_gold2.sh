# Query: Remove the last 3 characters from "987654321"

# @output "987654"
# @assume "echo \"987654321\"" --> "987654321"
# @assume "sed 's/...$//'" --> "987654"
echo "987654321" | sed 's/...$//'
