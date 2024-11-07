
#!/bin/sh

# Check if unzip command is available
if ! command -v unzip &> /dev/null
then
    echo "unzip command not found"
    exit
fi

# Specify the input .zip file and the output directory
unzip input.zip -d output_directory
