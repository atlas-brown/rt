
#!/bin/sh

# Search for files with specific permissions
find /path/to/directory -type f -perm 644 -exec ls -l {} \; > file_permissions_report.txt
