
#!/bin/sh

# List all files in the present working directory
ls -l | while read -r line; do
    # Get the file name
    file=$(echo $line | awk '{print $9}')
    # Get detailed information about the file
    stat $file
done
