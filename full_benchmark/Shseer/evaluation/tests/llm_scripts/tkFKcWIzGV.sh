
#!/bin/sh

# Function to generate random password
generate_password() {
  local length=$1
  local use_special_chars=$2
  local use_numbers=$3
  local use_uppercase=$4

  # Define character sets
  chars="abcdefghijklmnopqrstuvwxyz"
  special_chars="!@#$%^&*()_+{}|:<>?-=[]\;',./"
  numbers="0123456789"
  all_chars="${chars}"

  # Add special characters, numbers, and uppercase letters if requested
  if [ "$use_special_chars" = "true" ]; then
    all_chars="${all_chars}${special_chars}"
  fi
  if [ "$use_numbers" = "true" ]; then
    all_chars="${all_chars}${numbers}"
  fi
  if [ "$use_uppercase" = "true" ]; then
    all_chars="${all_chars}$(echo $chars | tr '[:lower:]' '[:upper:]')"
  fi

  # Generate password
  password=$(echo "$all_chars" | fold -w1 | shuf | tr -d '\n' | head -c $length)
  echo "$password"
}

# Get user input for password length and options
read -p "Enter password length: " length
read -p "Include special characters? (y/n): " special_chars
read -p "Include numbers? (y/n): " numbers
read -p "Include uppercase letters? (y/n): " uppercase

# Convert user input to lowercase
special_chars=$(echo "$special_chars" | tr '[:upper:]' '[:lower:]')
numbers=$(echo "$numbers" | tr '[:upper:]' '[:lower:]')
uppercase=$(echo "$uppercase" | tr '[:upper:]' '[:lower:]')

# Call the function to generate the password
generate_password $length $special_chars $numbers $uppercase
