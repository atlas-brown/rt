# Query: Calculate the md5 sum of all files in the /workspace directory with the filename printed first

find /workspace -type f -exec md5sum {} + | awk '{print $2 " " $1}'