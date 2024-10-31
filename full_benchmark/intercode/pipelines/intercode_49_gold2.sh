# Query: Recursively list contents of the '/system' directory in a tree-like format

find /system -print | sed -e 's;[^/]*/;|___;g;s;___|; |;g'