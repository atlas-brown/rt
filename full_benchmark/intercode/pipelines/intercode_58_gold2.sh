# Query: Recursively search for all regular files below directory "/system/folder3/", and output the name of each, without any containing directories.

find /system/folder3/ -type f | xargs -n 1 basename