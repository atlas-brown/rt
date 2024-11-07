
#!/bin/sh

# Check if logrotate command is installed
if ! command -v logrotate &> /dev/null
then
    echo "logrotate command not found. Please install logrotate."
    exit 1
fi

# Validate input arguments
if [ $# -ne 2 ]; then
    echo "Usage: $0 <logrotate_config_file> <log_directory>"
    exit 1
fi

config_file=$1
log_directory=$2

# Check if logrotate configuration file exists
if [ ! -f $config_file ]; then
    echo "Logrotate configuration file not found."
    exit 1
fi

# Check if log directory exists
if [ ! -d $log_directory ]; then
    echo "Log directory not found."
    exit 1
fi

# Rotate log files
logrotate -v $config_file
