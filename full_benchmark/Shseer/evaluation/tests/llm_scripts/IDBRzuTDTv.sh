
#!/bin/bash

# Define variables
username="newuser"
home_directory="/home/newuser"
additional_groups="group1,group2"

# Create new user account
useradd -m -d $home_directory -G $additional_groups $username

# Set password for the new user
passwd $username
