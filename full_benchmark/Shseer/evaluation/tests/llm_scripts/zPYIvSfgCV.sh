
#!/bin/sh

threshold=100M
logFile=cleanup.log

find / -type f -size +$threshold -exec rm -f {} \;
find / -type d -size +$threshold -exec rm -rf {} \;
echo "Deleted files and directories exceeding $threshold" >> $logFile
