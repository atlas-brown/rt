
#!/bin/sh

echo "Searching for possible vulnerabilities..."
find / -type f -perm -4000 -user root
