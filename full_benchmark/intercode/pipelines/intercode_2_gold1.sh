# Query: Calculate the md5 sum of the md5 sum of all the files under /testbed/dir2/subdir2 sorted by filename

find /testbed/dir2/subdir2 -type f -print0 | sort -z | xargs -0 md5sum | awk '{print $1}' | md5sum