# Query: Recursively removes all files in the /system/folder1 folder but '*txt' files.

find /system/folder1 -type f -not -name '*txt' | xargs rm