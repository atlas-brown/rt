# Query: Remove all *.txt files, except "keep.txt", under /system/folder1 directory modified more than 5 minutes ago. Do not include subdirectories.

find /system/folder1 -maxdepth 1 -mmin +5 -type f -name "*.txt" ! -name "keep.txt" | xargs rm -f