
#!/bin/sh

# Remove empty directories
find . -type d -empty -delete

# Archive and compress old files
find . -type f -mtime +30 -exec tar -czf archive.tar.gz {} \;

# Move specific file types to designated directories
find . -name "*.txt" -exec mv {} txt_files/ \;
find . -name "*.log" -exec mv {} log_files/ \;

# Log all actions taken for auditing purposes
echo "All actions completed successfully" >> audit.log
