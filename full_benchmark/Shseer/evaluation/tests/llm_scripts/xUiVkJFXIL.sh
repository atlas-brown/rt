
#!/bin/sh

# Prompt user for password length
echo "Enter the length of the password: "
read length

# Generate random password
password=$(openssl rand -base64 48 | head -c $length)

# Print the generated password
echo "Generated password: $password"
