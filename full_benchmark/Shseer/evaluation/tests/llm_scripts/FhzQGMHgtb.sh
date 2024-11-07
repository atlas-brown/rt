
#!/bin/sh

directory="/path/to/directory"
if [ -d "$directory" ]; then
    inotifywait -m -e modify,create,delete "$directory" >> event.log
else
    echo "Directory does not exist"
fi
