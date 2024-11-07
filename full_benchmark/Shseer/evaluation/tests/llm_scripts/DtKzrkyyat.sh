
#!/bin/bash

# Database credentials
DB_USER="username"
DB_PASS="password"
DB_NAME="database_name"

# Backup directory
BACKUP_DIR="/path/to/backup/directory"

# Current date and time
DATE=$(date +"%Y%m%d%H%M%S")

# Backup file name
BACKUP_FILE="$DB_NAME-$DATE.sql"

# Create backup
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME > $BACKUP_DIR/$BACKUP_FILE

# Compress backup file into zip archive
zip -r $BACKUP_DIR/$BACKUP_FILE.zip $BACKUP_DIR/$BACKUP_FILE

# Remove uncompressed backup file
rm $BACKUP_DIR/$BACKUP_FILE
