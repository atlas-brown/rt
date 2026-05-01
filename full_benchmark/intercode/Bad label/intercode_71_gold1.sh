# Query: Remove all empty files in /system/folder3/temp and below

find /system/folder3/temp -type f -empty -print | xargs rm -f