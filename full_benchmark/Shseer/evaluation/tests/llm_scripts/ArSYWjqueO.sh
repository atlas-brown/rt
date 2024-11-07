
#!/bin/sh

# Check available disk space
df -h > disk_space.log

# Set threshold for low disk space
threshold=90

# Check if disk space is running low
if [ $(df -h | awk 'NR==2 {print $5}' | cut -d'%' -f1) -ge $threshold ]; then
  # Delete old log files
  find /path/to/log/files -type f -mtime +7 -exec rm {} \;

  # Send email alert
  recipients="email1@example.com,email2@example.com"
  subject="Disk Space Alert"
  message="Disk space is running low on the server. Please take action immediately."
  echo "$message" | mail -s "$subject" "$recipients"
fi
