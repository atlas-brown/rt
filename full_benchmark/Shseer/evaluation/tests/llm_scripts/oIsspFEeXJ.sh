
#!/bin/bash

# Set the threshold for available disk space
threshold=90

# Get the available disk space using the df command and filter out the header
disk_space=$(df -h | awk 'NR>1 {print $5}' | sed 's/%//')

# Check if the available disk space is below the threshold
if [ $disk_space -ge $threshold ]; then
  # Send an email alert
  echo "Warning: Available disk space is below $threshold%" | mail -s "Disk Space Alert" user@example.com
fi
