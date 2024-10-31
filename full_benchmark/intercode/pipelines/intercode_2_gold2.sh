# Query: Calculate the md5 sum of the md5 sum of all the files under /testbed/dir2/subdir2 sorted by filename

ls -1 /testbed/dir2/subdir2/* | sort | xargs md5sum | awk '{print $1}' | md5sum