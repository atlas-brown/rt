# Query: Remove all *.txt files in '/system' directory but not in it's subdirectories

find /system -name '*.txt' -maxdepth 1 | xargs rm