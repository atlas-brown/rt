# Query: Recursively print all files and directories in the '/system/folder2' directory tree including hidden files

find /system/folder2 -print | sed -e 's;[^/]*/;|___;g;s;___|; |;g'