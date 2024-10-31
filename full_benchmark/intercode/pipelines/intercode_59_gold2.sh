# Query: Recursively unzip files to stdout in "/system/folder2.tar.gz" and search for "special"

tar -xzvf /system/folder2.tar.gz -O | grep "special"