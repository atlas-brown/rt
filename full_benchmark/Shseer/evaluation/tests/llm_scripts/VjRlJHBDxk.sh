
#!/bin/bash

# Define the log file path
log_file="/var/log/running_processes.log"

# Use the ps command to list all running processes and redirect the output to the log file
ps aux > "$log_file"

echo "Running processes have been logged to $log_file"
