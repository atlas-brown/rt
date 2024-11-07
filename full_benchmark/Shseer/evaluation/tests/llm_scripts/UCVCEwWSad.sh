
#!/bin/sh

cut -d: -f1,6 /etc/passwd | awk -F: '{print "User: " $1 ", Home Directory: " $2 ", Shell: " $NF}'
