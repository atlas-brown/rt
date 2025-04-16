# Query: Remove all *.txt files under the /system/folder1 directory modified more than 5 minutes ago

find /system/folder1 -mmin +5 -type f -name "*.txt" | xargs rm -f