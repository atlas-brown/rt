
#!/bin/sh

cat /etc/passwd | cut -d: -f1 | awk '{print $1}'
