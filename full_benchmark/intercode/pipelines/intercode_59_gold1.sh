# Query: Recursively unzip files to stdout in "/system/folder2.tar.gz" and search for "special"

zcat -r /system/folder2.tar.gz | grep "special"