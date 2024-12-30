# Query: Remove the last 3 characters from "987654321"

# @output "987654"
echo 987654321 | rev | cut -c 4- | rev
