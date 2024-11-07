
#!/bin/sh

# Prompt for username
read -p "Enter username: " username

# Prompt for home directory
read -p "Enter home directory: " home_dir

# Create user account
useradd -m -d $home_dir $username

# Set password for the new user
passwd $username
