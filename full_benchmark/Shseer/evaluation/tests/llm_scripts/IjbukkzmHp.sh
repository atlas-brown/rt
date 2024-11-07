
#!/bin/sh

# Use cat to retrieve the list of all users on the system
cat /etc/passwd | cut -d: -f1 | awk '{print $1}'
