
#!/bin/sh

# Define the directories to monitor
dir1="/path/to/dir1"
dir2="/path/to/dir2"

# Create separate log files for each directory
log1="dir1_log.txt"
log2="dir2_log.txt"

# Monitor dir1 for changes
inotifywait -m -r -e create,modify,delete "$dir1" | while read -r directory event file
do
    echo "Event: $event on $file" >> "$log1"
    # Perform actions based on event type
    case $event in
        CREATE)
            # Action for create event
            ;;
        MODIFY)
            # Action for modify event
            ;;
        DELETE)
            # Action for delete event
            ;;
    esac
done &

# Monitor dir2 for changes
inotifywait -m -r -e create,modify,delete "$dir2" | while read -r directory event file
do
    echo "Event: $event on $file" >> "$log2"
    # Perform actions based on event type
    case $event in
        CREATE)
            # Action for create event
            ;;
        MODIFY)
            # Action for modify event
            ;;
        DELETE)
            # Action for delete event
            ;;
    esac
done &
