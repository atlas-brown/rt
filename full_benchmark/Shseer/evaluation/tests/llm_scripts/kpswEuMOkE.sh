
#!/bin/sh

# Define the directory to monitor
directory_to_monitor="/path/to/directory"

# Define the log file
log_file="/path/to/log/file.log"

# Use inotifywait to monitor the directory for changes
inotifywait -m -e modify,create,delete "$directory_to_monitor" |
    while read path action file; do
        # Log the event to the log file
        echo "Change detected: $action on $file at $path" >> "$log_file"
    done
