
#!/bin/sh

# Retrieve the list of all users on the system
users=$(cut -d: -f1 /etc/passwd)

# Display the list of users, their home directories, and default shells
for user in $users
do
    home_directory=$(grep "^$user:" /etc/passwd | cut -d: -f6)
    default_shell=$(grep "^$user:" /etc/passwd | cut -d: -f7)
    echo "User: $user, Home Directory: $home_directory, Default Shell: $default_shell"
done
