
#!/bin/sh

# Check if the required command line arguments are provided
if [ $# -ne 3 ]; then
  echo "Usage: $0 <database_name> <username> <password>"
  exit 1
fi

# Assign the command line arguments to variables
database_name=$1
username=$2
password=$3

# Create a backup of the database
backup_file="backup_$(date +'%Y%m%d').sql"
mysqldump -u $username -p$password $database_name > $backup_file

# Check if the backup was successful
if [ $? -eq 0 ]; then
  echo "Backup of $database_name created successfully in $backup_file"
else
  echo "Backup of $database_name failed"
fi
