
#!/bin/sh

# Check available disk space
df -h > disk_space.log

# Send email alert
mail -s "Disk Space Alert" user1@example.com,user2@example.com < disk_space.log

# Automatically delete old log files if disk space is low
if [ $disk_space -lt 10 ]; then
    rm -f /var/log/*.log
fi
