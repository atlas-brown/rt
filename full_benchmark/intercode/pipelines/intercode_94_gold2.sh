# Query: Calculate the md5sum of each ".txt" file under "/system" and sort the output.

find /system -type f -name "*.txt" -exec md5sum {} + | sort