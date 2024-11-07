
#!/bin/sh

# Define the directories to be backed up
backup_directories="/path/to/directory1 /path/to/directory2"

# Define the files/subdirectories to be excluded
exclude_list="--exclude=/path/to/directory1/excluded_file --exclude=/path/to/directory2/excluded_directory"

# Create the backup using tar
tar -czf backup.tar.gz $exclude_list $backup_directories
