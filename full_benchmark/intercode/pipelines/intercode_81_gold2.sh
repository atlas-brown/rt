# Query: Print amount of space available on the file system containing path to the /system directory in megabytes.

# @assume "tr -s ' '" --> "[^ ]+ [0-9]+ [0-9]+ [0-9]+ [0-9]+% /.*"
df -m /system | grep / | tr -s ' ' | cut -d ' ' -f 4
