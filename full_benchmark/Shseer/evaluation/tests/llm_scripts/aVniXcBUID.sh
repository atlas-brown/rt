
#!/bin/bash

# Check for the correct number of arguments
if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <logrotate_config1> <directory1> [<logrotate_config2> <directory2> ...]"
  exit 1
fi

# Iterate through the arguments in pairs
for ((i=1; i<=$#; i+=2)); do
  logrotate_config="${!i}"
  directory="${!((i+1))}"

  # Check if the directory exists
  if [ ! -d "$directory" ]; then
    echo "Directory $directory does not exist"
    continue
  fi

  # Check if the logrotate configuration file exists
  if [ ! -f "$logrotate_config" ]; then
    echo "Logrotate configuration file $logrotate_config does not exist"
    continue
  fi

  # Rotate the log files using the logrotate configuration
  logrotate -v -f "$logrotate_config"

  # Compress and archive the rotated log files
  tar -czvf "${directory}_logs_$(date +"%Y%m%d").tar.gz" "${directory}"/*.1
done
