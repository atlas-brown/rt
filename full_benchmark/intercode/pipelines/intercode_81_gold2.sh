# Query: Print amount of space available on the file system containing path to the /system directory in megabytes.

df -m /system | grep / | tr -s ' ' | cut -d ' ' -f 4