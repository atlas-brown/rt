
#!/bin/sh

# Specify the directory to be backed up
backup_source="/path/to/source/directory"

# Specify the directory where the backup will be stored
backup_destination="/path/to/backup/directory"

# Check if the backup directory exists, and if not, create it
if [ ! -d "$backup_destination" ]; then
  mkdir -p "$backup_destination"
fi

# Create a timestamp for the backup file
timestamp=$(date +"%Y%m%d%H%M%S")

# Create the backup file with the timestamp
backup_file="$backup_destination/backup_$timestamp.tar.gz"
tar -czf "$backup_file" "$backup_source"

echo "Backup created at $backup_file"
