# Query: Write the current date and time followed by " 1" to the console and append to "/system/folder3/temp/empty.txt"

echo $(date +"%Y-%m-%d~%H:%M:%S") "1" | tee -a /system/folder3/temp/empty.txt