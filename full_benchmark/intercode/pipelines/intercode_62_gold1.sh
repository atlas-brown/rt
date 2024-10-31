# Query: Remove all *.log files from the /system/folder1 tree

find /system/folder1 -name '*.log' -print0 | xargs -0 rm