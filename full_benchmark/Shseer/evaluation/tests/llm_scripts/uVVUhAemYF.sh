
#!/bin/sh

# Search for setuid files owned by root
echo "Searching for setuid files owned by root..."
find / -type f -perm -4000 -user root -exec ls -l {} \;
