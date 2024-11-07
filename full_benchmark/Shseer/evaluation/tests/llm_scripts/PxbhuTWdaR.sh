
#!/bin/sh

# Get the current timestamp
timestamp=$(date +"%Y-%m-%d %T")

# Use the ps command to list processes owned by a specific user and append the output to a log file
ps -u <username> >> process_log.txt

# Append the timestamp to the log file
echo "Processes listed at $timestamp" >> process_log.txt
