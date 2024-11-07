
#!/bin/sh

# Specify the source directory and destination for the backup
source_dir="/path/to/source_directory"
backup_dir="/path/to/backup_directory/backup_$(date +'%Y%m%d').tar.gz"

# Create a compressed archive of the source directory, excluding specific files or directories
tar --exclude='/path/to/source_directory/exclude_file_or_directory' -czvf $backup_dir $source_dir

echo "Backup created at $backup_dir"
