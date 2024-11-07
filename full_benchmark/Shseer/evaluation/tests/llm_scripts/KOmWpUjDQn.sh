
#!/bin/sh

# Directories to be backed up
backup_dirs="/dir1 /dir2 /dir3"

# Exclude pattern
exclude_pattern="--exclude=/dir1/exclude_file --exclude=/dir2/exclude_dir"

# Create backup
tar -czvf backup.tar.gz $backup_dirs $exclude_pattern
